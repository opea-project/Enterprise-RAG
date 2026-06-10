# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import asyncio
import socket
import time
import threading
import concurrent.futures
from contextlib import contextmanager
from threading import Lock
from typing import Any
import requests
from requests.adapters import HTTPAdapter
import base64
import datetime
import subprocess  # nosec B404 — used only for qpdf (trusted local binary), calls are individually reviewed
import tempfile
from dotenv import load_dotenv
from minio.error import S3Error
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from celery import Celery, Task, shared_task
from app.models import FileStatus, LinkStatus
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from app.utils import get_local_minio_client

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "./.env"))

# Initialize the logger for the microservice
logger = get_opea_logger("edp_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

celery = Celery(
    "Celery",
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_BACKEND_URL', 'redis://localhost:6379/0'),
    task_ack_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1   # https://docs.celeryq.dev/en/latest/userguide/workers.html#max-tasks-per-child-setting
)

celery.conf.update(
    redis_backend_health_check_interval=10,
    redis_retry_on_timeout=True,
    redis_max_connections=10,
    redis_socket_timeout=120,  # increased from 30s — tasks can block on extractor for 30+ min, causing health-check pings to hit the old limit
    redis_socket_keepalive=True
)

HIERARCHICAL_DATAPREP_ENDPOINT  = os.environ.get('HIERARCHICAL_DATAPREP_ENDPOINT')
TEXT_EXTRACTOR_ENDPOINT  = os.environ.get('TEXT_EXTRACTOR_ENDPOINT')
TEXT_COMPRESSION_ENDPOINT  = os.environ.get('TEXT_COMPRESSION_ENDPOINT')
TEXT_SPLITTER_ENDPOINT  = os.environ.get('TEXT_SPLITTER_ENDPOINT')
EMBEDDING_ENDPOINT = os.environ.get('EMBEDDING_ENDPOINT')
EMBEDDING_MODEL_NAME = os.environ.get('EMBEDDING_MODEL_NAME', 'unknown')
LATE_CHUNKING_ENDPOINT = os.environ.get('LATE_CHUNKING_ENDPOINT')
INGESTION_ENDPOINT = os.environ.get('INGESTION_ENDPOINT')
EMBEDDING_TIMEOUT = int(os.getenv('EMBEDDING_TIMEOUT_SECONDS', '120'))
TEXT_PROCESSING_TIMEOUT_SECONDS = int(os.getenv('TEXT_PROCESSING_TIMEOUT_SECONDS', '300'))  # timeout for compression and splitter requests
TEXT_EXTRACTOR_TIMEOUT_SECONDS = int(os.getenv('TEXT_EXTRACTOR_TIMEOUT_SECONDS', '900'))  # timeout per extractor request (default 15 min — applies to both single files and per-part in pipelined extraction; small files are fast, large ones are split into ≤100-page chunks)
MAX_PAGES_PER_SPLIT = int(os.getenv('MAX_PAGES_PER_SPLIT', '100'))  # max pages per PDF part for parallel extraction across replicas
MIN_PAGES_TO_SPLIT = int(os.getenv('MIN_PAGES_TO_SPLIT', '100'))  # don't split PDFs smaller than this — overhead isn't worth it
MAX_EXTRACTOR_WORKERS = int(os.getenv('MAX_EXTRACTOR_WORKERS', '8'))  # max concurrent extractor threads; also used as target part count for pod distribution

# ---------------------------------------------------------------------------
# TCP keep-alive adapter --  kube-proxy (IPVS mode) drops idle connections
# after its TCP established timeout (default 900 s / 15 min).  Long-running
# extractor requests (30+ min for large PDFs) sit idle while the extractor
# processes pages, so the IPVS entry expires and the response is silently
# dropped.  Sending TCP keep-alive probes every 60 s keeps the connection
# alive through the IPVS timeout.
# ---------------------------------------------------------------------------
_TCP_KEEPIDLE  = int(os.getenv('TCP_KEEPIDLE',  '60'))   # seconds before first keep-alive probe
_TCP_KEEPINTVL = int(os.getenv('TCP_KEEPINTVL', '60'))   # seconds between probes
_TCP_KEEPCNT   = int(os.getenv('TCP_KEEPCNT',    '5'))   # failed probes before giving up


class KeepAliveAdapter(HTTPAdapter):
    """HTTPAdapter that enables TCP keep-alive on every connection."""
    def init_poolmanager(self, *args, **kwargs):
        kwargs.setdefault('socket_options', [
            (socket.SOL_SOCKET,  socket.SO_KEEPALIVE,  1),
            (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE,  _TCP_KEEPIDLE),
            (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, _TCP_KEEPINTVL),
            (socket.IPPROTO_TCP, socket.TCP_KEEPCNT,   _TCP_KEEPCNT),
        ])
        super().init_poolmanager(*args, **kwargs)


def _keepalive_session() -> requests.Session:
    """Return a requests.Session with TCP keep-alive enabled."""
    s = requests.Session()
    adapter = KeepAliveAdapter()
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    return s


class WithEDPTask(Task):

    def __init__(self):
        self.sessions = {}
        self._minio = None
        self._engine = None

        if self._minio is None:
            self._minio = get_local_minio_client()

        if self._engine is None:
            DATABASE_USER = os.getenv("DATABASE_USER")
            DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
            DATABASE_HOST = os.getenv("DATABASE_HOST", 'postgres')
            DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
            DATABASE_NAME = os.getenv("DATABASE_NAME",'enhanced_dataprep')
            DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
            self._engine = create_engine(DATABASE_URL, pool_size=8, max_overflow=8, pool_pre_ping=True)  # pool_pre_ping detects stale connections after long extractor waits

    def before_start(self, task_id, args, kwargs):
        self.sessions[task_id] = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)()
        super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        session = self.sessions.pop(task_id)
        session.close()
        super().after_return(status, retval, task_id, args, kwargs, einfo)

    @property
    def db(self):
        return self.sessions[self.request.id] # equal to task_id

    @property
    def minio(self):
        return self._minio

    @contextmanager
    def db_keepalive(self, interval=60):
        """Periodically ping the DB via the engine (thread-safe) so PostgreSQL
        does not close the idle connection during long-running HTTP calls
        (e.g. extraction that can take 30+ min).

        On exit, invalidates the session's connection and forces a reconnect
        via a lightweight query.  This keeps the same session object so ORM
        objects remain attached and thread-safety characteristics are unchanged.
        """
        stop = threading.Event()
        def _ping():
            while not stop.wait(interval):
                try:
                    with self._engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    logger.debug("DB keepalive ping OK.")
                except Exception:
                    logger.warning("DB keepalive ping failed.")
        t = threading.Thread(target=_ping, daemon=True)
        t.start()
        try:
            yield
        finally:
            stop.set()
            t.join(timeout=5)
            # Invalidate and reconnect the session's connection.
            # rollback() releases the (possibly stale) connection back to the
            # pool; the next execute() transparently gets a fresh one
            # (pool_pre_ping=True validates it).
            try:
                self.db.rollback()
                self.db.execute(text("SELECT 1"))
                logger.info("DB session reconnected after long extraction wait.")
            except Exception as e:
                logger.warning(f"DB session reconnect failed ({e}), will retry on next use.")

    def safe_commit(self):
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error committing to database: {e}")
            try:
                self.db.rollback()
            except Exception:
                logger.warning("Rollback failed on dead connection.")
            raise e

def response_err(response):
    try:
        return response.json().get('detail', response.text)
    except Exception:
        return response.text


def _prepare_pdf_temp(file_data):
    """Write PDF bytes to a temp file and count pages via qpdf.

    Returns ``(tmp_path, total_pages)``.  The caller owns ``tmp_path`` and
    must delete it when done.  Raises an Exception on qpdf failure (e.g.
    malformed or password-protected PDF), including qpdf's stderr output.
    """
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.pdf')
    success = False
    try:
        os.write(tmp_fd, file_data)
        os.close(tmp_fd)
        result = subprocess.run(  # nosec
            ['qpdf', '--show-npages', tmp_path],
            capture_output=True, text=True, check=True,
        )
        success = True
    except subprocess.CalledProcessError as e:
        raise Exception(e.stderr.strip() or str(e))
    finally:
        if not success:
            try:
                os.unlink(tmp_path)
            except OSError as e:
                logger.warning(f"Failed to clean up temp PDF {tmp_path}: {e}")
    return tmp_path, int(result.stdout.strip())


def _split_pdf(file_data, max_pages):
    """Check if a PDF needs splitting and return page count info.

    Returns ``(needs_split: bool, total_pages: int)``.
    Uses qpdf --show-npages for fast page counting.
    """
    tmp_path, total_pages = _prepare_pdf_temp(file_data)
    try:
        return total_pages > max_pages, total_pages
    finally:
        try:
            os.unlink(tmp_path)
        except OSError as e:
            logger.warning(f"Failed to clean up temp PDF {tmp_path}: {e}")


def _resolve_extractor_pods(endpoint):
    """Resolve extractor pod IPs by doing a DNS lookup on the endpoint's hostname.

    When TEXT_EXTRACTOR_ENDPOINT points to a headless service, Kubernetes DNS
    returns one A record per pod, enabling direct per-pod routing.  Falls back
    to [endpoint] if DNS resolution fails.
    Returns a list of full URLs (e.g. ['http://10.0.0.1:9398/v1/text_extractor', ...]).
    """
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(endpoint)
    host = parsed.hostname
    port = parsed.port or 9398

    try:
        addrs = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        pod_ips = sorted(set(addr[4][0] for addr in addrs))

        if not pod_ips:
            logger.warning(f"DNS returned 0 IPs for {host}, using original endpoint")
            return [endpoint]

        pod_endpoints = [
            urlunparse(parsed._replace(netloc=f"{ip}:{port}"))
            for ip in pod_ips
        ]
        logger.info(f"Resolved {len(pod_endpoints)} extractor pods via {host}: {pod_ips}")
        return pod_endpoints
    except Exception as e:
        logger.warning(f"Failed to resolve {host}: {e}. Using original endpoint.")
        return [endpoint]


def _split_pdf_part(src_path, file_name, file_id, part_index, max_pages, total_pages, total_parts):
    """Split one page range from a PDF using qpdf and return its base64 content."""
    t_part = time.monotonic()
    start_page = part_index * max_pages + 1  # qpdf uses 1-based pages
    end_page = min(part_index * max_pages + max_pages, total_pages)

    tmp_out_fd, tmp_out_path = tempfile.mkstemp(suffix='.pdf')
    os.close(tmp_out_fd)
    try:
        try:
            subprocess.run(  # nosec
                ['qpdf', src_path, '--pages', src_path,
                 f'{start_page}-{end_page}', '--', tmp_out_path],
                check=True, capture_output=True, text=True,
            )
        except subprocess.CalledProcessError as e:
            raise Exception(
                f"qpdf failed splitting '{file_name}' part {part_index + 1}/{total_parts} "
                f"(pages {start_page}-{end_page}): {e.stderr.strip() or str(e)}"
            )
        with open(tmp_out_path, 'rb') as f:
            part_bytes = f.read()
    finally:
        try:
            os.unlink(tmp_out_path)
        except OSError as e:
            logger.warning(f"Failed to clean up temp PDF part {tmp_out_path}: {e}")

    part_b64 = base64.b64encode(part_bytes).decode('ascii')
    logger.info(
        f"[{file_id}] Split part {part_index + 1}/{total_parts} "
        f"pages {start_page}-{end_page} ({end_page - start_page + 1} pages, "
        f"{len(part_bytes) / (1024*1024):.1f} MB, "
        f"{time.monotonic() - t_part:.1f}s) [qpdf]"
    )
    return part_b64


def _send_extraction_part(file_id, file_name, part_index, total_parts,
                          part_b64, target_endpoint, timeout, response_key):
    """Send a single PDF part to an extractor pod and return (part_index, docs)."""
    stem, ext = os.path.splitext(file_name)
    part_label = f"{stem}_part{part_index + 1}of{total_parts}{ext}"
    http = _keepalive_session()
    # Bypass corporate HTTP proxy for direct pod-IP requests —
    # the proxy cannot reach cluster-internal pod IPs and returns 403.
    http.trust_env = False
    part_size_mb = len(part_b64) * 3 / 4 / (1024 * 1024)
    logger.info(
        f"[{file_id}] Sending {part_label} ({part_size_mb:.1f} MB) "
        f"to {target_endpoint} (timeout={timeout}s)"
    )
    t_start = time.monotonic()
    resp = http.post(
        target_endpoint,
        json={'files': [{'filename': file_name, 'data64': part_b64}]},
        timeout=timeout,
    )
    elapsed = time.monotonic() - t_start
    if resp.status_code != 200:
        logger.error(f"[{file_id}] {part_label}: extractor returned {resp.status_code} after {elapsed:.1f}s")
        raise Exception(f"Extraction failed for {part_label}: {response_err(resp)}")
    docs = resp.json().get(response_key, [])
    logger.info(f"[{file_id}] {part_label}: extracted {len(docs)} docs in {elapsed:.1f}s")
    return part_index, docs


def _split_and_extract_pipelined(file_id, file_name, file_data, max_pages,
                                  endpoint, timeout, response_key,
                                  prebuilt_parts=None):
    """Split a large PDF and extract parts across extractor pods in parallel.

    Splits are done serially in the main thread (qpdf temp-file I/O), while
    HTTP sends happen concurrently in a thread pool.  As soon as a split
    finishes, the part is dispatched to the next available pod.  After all
    parts are dispatched, remaining extractions are awaited with
    FIRST_COMPLETED semantics so no pod sits idle.

    Args:
        file_data: raw PDF bytes (unused if prebuilt_parts is set)
        max_pages: pages per split part (unused if prebuilt_parts is set)
        prebuilt_parts: if set, skip splitting and use these base64 parts directly
    """
    # ------------------------------------------------------------------
    # Phase 1: determine total parts and prepare temp file
    # ------------------------------------------------------------------
    if prebuilt_parts is not None:
        total_parts = len(prebuilt_parts)
        total_pages = None
        logger.info(f"[{file_id}] Pipelined extraction with {total_parts} pre-built parts")
        _tmp_pdf_path = None
    else:
        t_read = time.monotonic()
        try:
            _tmp_pdf_path, total_pages = _prepare_pdf_temp(file_data)
        except Exception as e:
            raise Exception(f"qpdf could not read '{file_name}': {e}")
        total_parts = (total_pages + max_pages - 1) // max_pages
        logger.info(
            f"[{file_id}] Pipelined split+extract: {total_pages} pages → "
            f"{total_parts} parts of up to {max_pages} pages "
            f"(read took {time.monotonic() - t_read:.1f}s)"
        )

    # ------------------------------------------------------------------
    # Phase 2: dispatch parts to pods
    # ------------------------------------------------------------------
    results = {}
    completed_count = 0

    pod_endpoints = _resolve_extractor_pods(endpoint)
    num_pods = len(pod_endpoints)
    known_pod_ips = set(pod_endpoints)

    logger.info(
        f"[{file_id}] Dispatching {total_parts} parts across {num_pods} pods "
        f"(serial-split, parallel-send)"
    )

    max_workers = max(num_pods, min(total_parts, MAX_EXTRACTOR_WORKERS))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        pending = set()
        future_map = {}   # future → (part_idx, pod_idx)
        pod_queue = list(range(num_pods))

        def _submit(part_idx, pod_idx, part_b64):
            future = executor.submit(
                _send_extraction_part, file_id, file_name, part_idx,
                total_parts, part_b64, pod_endpoints[pod_idx], timeout, response_key,
            )
            pending.add(future)
            future_map[future] = (part_idx, pod_idx)

        def _refresh_pods():
            nonlocal num_pods
            fresh = _resolve_extractor_pods(endpoint)
            new_pods = [ep for ep in fresh if ep not in known_pod_ips]
            if new_pods:
                for ep in new_pods:
                    pod_endpoints.append(ep)
                    known_pod_ips.add(ep)
                    pod_queue.append(len(pod_endpoints) - 1)
                num_pods = len(pod_endpoints)
                logger.info(
                    f"[{file_id}] Discovered {len(new_pods)} new extractor pod(s) "
                    f"via HPA, now {num_pods} pods total"
                )

        def _collect_done(futures_done):
            nonlocal completed_count
            for f in futures_done:
                pending.discard(f)
                p_idx, p_pod = future_map[f]
                idx, docs = f.result()  # raises on error
                results[idx] = docs
                completed_count += 1
                pod_queue.append(p_pod)
                logger.info(
                    f"[{file_id}] Parallel extraction progress: "
                    f"{completed_count}/{total_parts} parts done"
                )

        # Split each part in main thread, dispatch send immediately
        for part_idx in range(total_parts):
            if prebuilt_parts is not None:
                part_b64 = prebuilt_parts[part_idx]
            else:
                part_b64 = _split_pdf_part(
                    _tmp_pdf_path, file_name, file_id,
                    part_idx, max_pages, total_pages, total_parts,
                )

            # Collect any already-finished futures
            _collect_done({f for f in list(pending) if f.done()})

            if not pod_queue:
                _refresh_pods()

            # Wait for a free pod if all are busy
            while not pod_queue:
                if not pending:
                    break
                done_set, _ = concurrent.futures.wait(
                    pending, return_when=concurrent.futures.FIRST_COMPLETED,
                )
                _collect_done(done_set)
                if not pod_queue:
                    _refresh_pods()

            pod_idx = pod_queue.pop(0)
            _submit(part_idx, pod_idx, part_b64)

        # Wait for remaining extractions
        first_error = None
        while pending:
            done, pending = concurrent.futures.wait(
                pending, return_when=concurrent.futures.FIRST_COMPLETED,
            )
            for future in done:
                part_idx, pod_idx = future_map[future]
                try:
                    idx, docs = future.result()
                    results[idx] = docs
                    completed_count += 1
                    logger.info(
                        f"[{file_id}] Parallel extraction progress: "
                        f"{completed_count}/{total_parts} parts done"
                    )
                except Exception as e:
                    logger.error(f"[{file_id}] Part {part_idx + 1}/{total_parts} failed: {e}")
                    if first_error is None:
                        first_error = e
                        for f in pending:
                            f.cancel()
                        pending.clear()
                        break

    if first_error:
        logger.error(f"[{file_id}] Pipelined extraction failed: {first_error}")
        raise first_error

    # Clean up temp PDF file
    if _tmp_pdf_path:
        try:
            os.unlink(_tmp_pdf_path)
        except OSError as e:
            logger.warning(f"Failed to clean up temp PDF {_tmp_pdf_path}: {e}")

    # Merge results in original page order
    merged = []
    for i in range(total_parts):
        merged.extend(results[i])

    logger.info(f"[{file_id}] Merged {len(merged)} docs from {total_parts} parts across {num_pods} pods")
    return merged


@shared_task(base=WithEDPTask, bind=True)
def process_file_task(self, file_id: Any, *args, **kwargs):

    file_db = self.db.query(FileStatus).filter(FileStatus.id == file_id).first()
    if file_db is None:
        raise Exception(f"File with id {file_id} not found")

    if file_db.marked_for_deletion is True:
        logger.info(f"[{file_db.id}] File is marked for deletion, skipping processing.")
        return False

    logger.debug(f"[{file_db.id}] Started processing file.")

    file_db.status = 'processing'
    file_db.job_message = 'Data clean up in progress.'
    self.safe_commit()

    # Step 0 - Delete everything related to the file in the vector database
    response = requests.post(f"{INGESTION_ENDPOINT}/delete", json={ 'file_id': str(file_db.id) })
    if response.status_code != 200:
        file_db.status = 'error'
        file_db.job_message = f"Error encountered while removing existing data related to file. {response_err(response)}"
        self.safe_commit()
        raise Exception(f"Error encountered while data clean up. {response_err(response)}")
    logger.debug(f"[{file_db.id}] Deleted existing data related to file.")

    # Step 1 - Prepare the file for text_extractor request
    file_db.text_extractor_start = datetime.datetime.now()
    file_db.status = 'text_extracting'
    file_db.job_message = 'Data loading in progress.'
    self.safe_commit()

    minio_response = None
    file_base64 = None
    try:
        if file_db.site_name:
            # SharePoint-sourced file — download from SP on demand
            from app.sharepoint import download_sp_file_by_path
            from app.models import SharePointSiteRecord
            from sqlalchemy import or_
            sp_record = self.db.query(SharePointSiteRecord).filter(
                or_(
                    SharePointSiteRecord.display_name == file_db.site_name,
                    SharePointSiteRecord.name == file_db.site_name,
                )
            ).first()
            if not sp_record:
                raise Exception(f"SharePoint site record not found for site_name='{file_db.site_name}'")
            file_data = asyncio.run(download_sp_file_by_path(sp_record.graph_site_id, file_db.object_name))
            file_base64 = base64.b64encode(file_data).decode('ascii')
            logger.debug(f"[{file_db.id}] Retrieved file from SharePoint site '{file_db.site_name}'.")
        else:
            minio_response = self.minio.get_object(bucket_name=file_db.bucket_name, object_name=file_db.object_name)
            file_data = minio_response.read()
            file_base64 = base64.b64encode(file_data).decode('ascii')
            logger.debug(f"[{file_db.id}] Retrieved file from S3 storage.")
    except S3Error as e:
        if e.code == 'NoSuchKey':
            # File was deleted from storage before this task ran (delete-then-reprocess race).
            # Mark the DB record as deleted so the UI doesn't show a spurious error.
            logger.warning(f"[{file_db.id}] File no longer exists in S3 ({file_db.object_name}), marking as deleted.")
            file_db.status = 'deleted'
            file_db.job_message = 'File was removed from storage before processing could start.'
            file_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            return False
        file_db.status = 'error'
        file_db.job_message = f"Error downloading file. {e}"
        file_db.text_extractor_end = datetime.datetime.now()
        self.safe_commit()
        raise Exception(f"Error downloading file. {e}")
    finally:
        if minio_response is not None:
            minio_response.close()
            minio_response.release_conn()

    # Step 2 - Call the text extractor service
    file_name = os.path.basename(file_db.object_name)
    http = _keepalive_session()  # TCP keep-alive prevents IPVS from dropping the idle connection during long extractions
    dataprep_docs = []

    # --- Check if PDF should be split for parallel extraction across pods ---
    needs_split = False
    effective_max_pages = MAX_PAGES_PER_SPLIT
    if file_name.lower().endswith('.pdf'):
        try:
            needs_split, pdf_total_pages = _split_pdf(file_data, MAX_PAGES_PER_SPLIT)

            # Even if the PDF is under MAX_PAGES_PER_SPLIT, split it across
            # extractor pods so all replicas share the load.
            # Use the *current* pod count but also ensure we always create
            # enough parts for the HPA max — pods can scale up at any time
            # and the dispatcher (_refresh_pods) will discover them.
            if not needs_split and pdf_total_pages >= MIN_PAGES_TO_SPLIT:
                current_pods = len(_resolve_extractor_pods(TEXT_EXTRACTOR_ENDPOINT))
                # Aim for at least as many parts as the max expected pods
                # (current count may be 1 if HPA hasn't scaled yet).
                target_parts = max(current_pods, MAX_EXTRACTOR_WORKERS)
                pages_per_part = max(MIN_PAGES_TO_SPLIT, (pdf_total_pages + target_parts - 1) // target_parts)
                if pages_per_part < pdf_total_pages:
                    effective_max_pages = pages_per_part
                    needs_split = True
                    actual_parts = (pdf_total_pages + pages_per_part - 1) // pages_per_part
                    logger.info(
                        f"[{file_db.id}] PDF {file_name}: {pdf_total_pages} pages, "
                        f"splitting into {actual_parts} parts of ~{pages_per_part} pages "
                        f"(current pods={current_pods}, target_parts={target_parts})"
                    )

            if needs_split:
                if effective_max_pages == MAX_PAGES_PER_SPLIT:
                    logger.info(f"[{file_db.id}] PDF {file_name}: {pdf_total_pages} pages > {MAX_PAGES_PER_SPLIT} limit, will split+extract in pipeline")
            else:
                logger.info(f"[{file_db.id}] PDF {file_name}: {pdf_total_pages} pages, no split needed")
        except Exception as e:
            logger.warning(f"[{file_db.id}] PDF page count check failed, falling back to single request: {e}")
            needs_split = False

    if HIERARCHICAL_DATAPREP_ENDPOINT is not None and HIERARCHICAL_DATAPREP_ENDPOINT != "":
        logger.info(f"[{file_db.id}] Hierarchical Dataprep endpoint is set. Using it for dataprep.")
        try:
            with self.db_keepalive():
                response = http.post(HIERARCHICAL_DATAPREP_ENDPOINT, json={ 'files': [{'filename': file_name, 'data64': file_base64}] }, timeout=TEXT_EXTRACTOR_TIMEOUT_SECONDS)
        except requests.exceptions.ConnectionError as e:
            file_db.status = 'error'
            file_db.job_message = f"Connection error while calling hierarchical dataprep service (service may have restarted). {e}"
            file_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Connection error while calling hierarchical dataprep service. {e}")
        except Exception as e:
            file_db.status = 'error'
            file_db.job_message = f"Unexpected error while calling hierarchical dataprep service. {e}"
            file_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise
        if response.status_code != 200:
            file_db.status = 'error'
            file_db.job_message = f"Error encountered while data preparation. {response_err(response)}"
            file_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while data preparation. {response_err(response)}")
        logger.debug(f"[{file_db.id}] Data preparation completed.")

        try:
            dataprep_docs = response.json()['docs']
            if len(dataprep_docs) == 0:
                logger.debug(f"[{file_db.id}] Data preparation returned 0 chunks.")
                raise Exception('No text extracted from the file.')

            file_db.chunk_size = len(dataprep_docs[0]) # Update chunk size
            file_db.chunks_total = len(dataprep_docs) # Update chunks count
            file_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
        except Exception as e:
            file_db.status = 'error'
            file_db.job_message = 'No text extracted from the file.'
            file_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error parsing response from data preparation service. {e} {response.text}")
    else:
        text_extractor_docs = []

        if needs_split:
            logger.info(f"[{file_db.id}] Using pipelined split+extract for {file_name} ({pdf_total_pages} pages, max {effective_max_pages} per part).")
            try:
                with self.db_keepalive():
                    text_extractor_docs = _split_and_extract_pipelined(
                        file_id=str(file_db.id),
                        file_name=file_name,
                        file_data=file_data,
                        max_pages=effective_max_pages,
                        endpoint=TEXT_EXTRACTOR_ENDPOINT,
                        timeout=TEXT_EXTRACTOR_TIMEOUT_SECONDS,
                        response_key='loaded_docs',
                    )
            except requests.exceptions.ConnectionError as e:
                file_db.status = 'error'
                file_db.job_message = f"Connection error while calling text extractor service (service may have restarted). {e}"
                file_db.text_extractor_end = datetime.datetime.now()
                self.safe_commit()
                raise Exception(f"Connection error while calling text extractor service. {e}")
            except Exception as e:
                file_db.status = 'error'
                file_db.job_message = f"Unexpected error while calling text extractor service. {e}"
                file_db.text_extractor_end = datetime.datetime.now()
                self.safe_commit()
                raise

            if len(text_extractor_docs) == 0:
                file_db.status = 'error'
                file_db.job_message = 'No text extracted from the file.'
                file_db.text_extractor_end = datetime.datetime.now()
                self.safe_commit()
                raise Exception('No text extracted from the file.')
            file_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            logger.info(f"[{file_db.id}] Pipelined extraction completed: {len(text_extractor_docs)} docs.")
        else:
            logger.info(f"[{file_db.id}] Calling text extractor (file={file_name}, timeout={TEXT_EXTRACTOR_TIMEOUT_SECONDS}s).")
            try:
                with self.db_keepalive():
                    response = http.post(TEXT_EXTRACTOR_ENDPOINT, json={ 'files': [{'filename': file_name, 'data64': file_base64}] }, timeout=TEXT_EXTRACTOR_TIMEOUT_SECONDS)
            except requests.exceptions.ConnectionError as e:
                file_db.status = 'error'
                file_db.job_message = f"Connection error while calling text extractor service (service may have restarted). {e}"
                file_db.text_extractor_end = datetime.datetime.now()
                self.safe_commit()
                raise Exception(f"Connection error while calling text extractor service. {e}")
            except Exception as e:
                file_db.status = 'error'
                file_db.job_message = f"Unexpected error while calling text extractor service. {e}"
                file_db.text_extractor_end = datetime.datetime.now()
                self.safe_commit()
                raise
            if response.status_code != 200:
                file_db.status = 'error'
                file_db.job_message = f"Error encountered while data loading. {response_err(response)}"
                file_db.text_extractor_end = datetime.datetime.now()
                self.safe_commit()
                raise Exception(f"Error encountered while data loading. {response_err(response)}")
            logger.info(f"[{file_db.id}] Data loading completed.")

            try:
                text_extractor_docs = response.json()['loaded_docs']
                if len(text_extractor_docs) == 0:
                    logger.debug(f"[{file_db.id}] Data loading returned 0 documents.")
                    raise Exception('No text extracted from the file.')
                file_db.text_extractor_end = datetime.datetime.now()
                self.safe_commit()
            except Exception as e:
                file_db.status = 'error'
                file_db.job_message = 'No text extracted from the file.'
                file_db.text_extractor_end = datetime.datetime.now()
                self.safe_commit()
                raise Exception(f"Error parsing response from data loading service. {e} {response.text}")

        # Step 3 - Call the text compression service to compress the documents
        file_db.text_compression_start = datetime.datetime.now()
        file_db.status = 'text_compression'
        file_db.job_message = 'Text compression in progress.'
        self.safe_commit()
        logger.info(f"[{file_db.id}] Starting text compression ({len(text_extractor_docs)} docs).")

        response = requests.post(TEXT_COMPRESSION_ENDPOINT, json={ 'loaded_docs': text_extractor_docs }, timeout=TEXT_PROCESSING_TIMEOUT_SECONDS)
        if response.status_code != 200:
            file_db.status = 'error'
            file_db.job_message = f"Error encountered while text compressing. {response_err(response)}"
            file_db.text_compression_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while text compressing. {response_err(response)}")
        logger.info(f"[{file_db.id}] Text compression completed.")

        dataprep_compressed_docs = []
        try:
            dataprep_compressed_docs = response.json()['loaded_docs']
            if len(dataprep_compressed_docs) == 0:
                logger.debug(f"[{file_db.id}] Text compression returned 0 documents.")
                raise Exception('No text compressed.')
            file_db.chunk_size = len(dataprep_compressed_docs[0]) # Update chunk size
            file_db.chunks_total = len(dataprep_compressed_docs) # Update chunks count
            file_db.text_compression_end = datetime.datetime.now()
            self.safe_commit()
        except Exception as e:
            file_db.status = 'error'
            file_db.job_message = 'No text compressed.'
            file_db.text_compression_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error parsing response from text compression service. {e} {response.text}")

        # Step 4 - Call the data splitter service to split the documents into smaller chunks
        file_db.text_splitter_start = datetime.datetime.now()
        file_db.status = 'text_splitting'
        file_db.job_message = 'Data splitting in progress.'
        self.safe_commit()
        logger.info(f"[{file_db.id}] Starting text splitting ({len(dataprep_compressed_docs)} docs).")

        late_chunking_enabled = os.getenv('LATE_CHUNKING_ENABLED', "false").lower()
        additional_params = {}
        if late_chunking_enabled == "true":
            additional_params = { 'chunk_size': 8192, 'chunk_overlap': 1024 }
        
        response = requests.post(TEXT_SPLITTER_ENDPOINT, json={ 'loaded_docs': dataprep_compressed_docs, **additional_params }, timeout=TEXT_PROCESSING_TIMEOUT_SECONDS)
        if response.status_code != 200:
            file_db.status = 'error'
            file_db.job_message = f"Error encountered while data splitting. {response_err(response)}"
            file_db.text_splitter_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while data splitting. {response_err(response)}")
        logger.info(f"[{file_db.id}] Data splitting completed.")

        try:
            dataprep_docs = response.json()['docs']
            if len(dataprep_docs) == 0:
                logger.debug(f"[{file_db.id}] Data splitting returned 0 chunks.")
                raise Exception('No text extracted from the file.')
            file_db.chunk_size = len(dataprep_docs[0]) # Update chunk size
            file_db.chunks_total = len(dataprep_docs) # Update chunks count
            file_db.text_splitter_end = datetime.datetime.now()
            self.safe_commit()
        except Exception as e:
            file_db.status = 'error'
            file_db.job_message = 'No text extracted from the file.'
            file_db.text_splitter_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error parsing response from data splitting service. {e} {response.text}")

    # 4.1 Update the metadata info from database
    for doc in dataprep_docs:
        doc['metadata']['etag'] = file_db.etag
        if file_db.site_name:
            doc['metadata']['site_name'] = file_db.site_name
        else:
            doc['metadata']['bucket_name'] = file_db.bucket_name
        doc['metadata']['object_name'] = file_db.object_name
        doc['metadata']['file_id'] = str(file_db.id).replace('-', '') # uuid w/o hyphens because redis does not support search with hypens

    # Step 4.5 (Optional) - scan datapreped documents with Dataprep Guardrail, after calling fingerprint for configuration
    dpguard_msg = ""
    dpguard_status = ""
    try:
        dpguard_enabled = os.getenv('DPGUARD_ENABLED', "false")
        logger.info(f"dpguard_enabled: {dpguard_enabled}")
        if dpguard_enabled == "true":
            file_db.dpguard_start = datetime.datetime.now()
            file_db.status = 'dpguard'
            file_db.job_message = 'Data Preparation Guardrail in progress.'
            self.safe_commit()

            # Step 4.5.1 - call fingerprint for configuration
            fingerprint_endpoint   = os.environ.get('FINGERPRINT_ENDPOINT')
            logger.info(f"fingerprint_endpoint: {fingerprint_endpoint}")
            logger.info("Reaching to fingerprint for dataprep guard configuration.")
            fprint_response = requests.post(fingerprint_endpoint, json={ 'text': "" })
            dpguard_params = fprint_response.json().get("parameters")['dataprep_guardrail_params']

            dpguard_endpoint   = os.environ.get('DPGUARD_ENDPOINT')
            logger.debug(f"Reaching dataprep guard endpoint: {dpguard_endpoint} with dataprep guardrail params: {dpguard_params}")
            logger.info("Dataprep Guardrail enabled. Scanning the documents.")
            response = requests.post(dpguard_endpoint,
                                     json={ 'docs': dataprep_docs, 'dataprep_guardrail_params': dpguard_params })
            if response.status_code != 200:
                dpguard_msg = 'Dataprep Guardrail failed.'
                dpguard_status = 'error'
                if response.status_code == 466:
                    dpguard_msg = "Dataprep Guardrail blocked embedding this document"
                    dpguard_status = 'blocked'
                raise Exception(f"{dpguard_msg} {response_err(response)}")
            file_db.dpguard_end = datetime.datetime.now()
            self.safe_commit()
            logger.info("Dataprep Guardrail completed.")
    except Exception as e:
        file_db.job_message = dpguard_msg if dpguard_msg else 'Error while executing dataprep guardrail.'
        file_db.status = dpguard_status if dpguard_status else 'error'
        file_db.dpguard_end = datetime.datetime.now()
        self.safe_commit()
        raise Exception(f"Error while executing dataprep guardrail. {e} {response.text}")

    if late_chunking_enabled == "true":
        # Step 5 - Call the late chunking service and ingestion service
        batch_size = 1 # sending requests individually due to TorchServe serialization issues
        file_db.late_chunking_start = datetime.datetime.now()
        file_db.ingestion_start = file_db.late_chunking_start
        file_db.status = 'late_chunking'
        file_db.job_message = 'Data late chunking in progress.'
        self.safe_commit()
        total_late_chunking_duration = datetime.timedelta()
        total_ingestion_duration = datetime.timedelta()
        final_chunk_number = 0
        final_chunk_size = 0
        
        for i in range(0, len(dataprep_docs), batch_size):
            # Step 5.1 - send each chunk of text from dataprep to the late chunking service
            docs_batch = dataprep_docs[i:i+batch_size]
            
            start_late_chunking_time = datetime.datetime.now()
            response = requests.post(LATE_CHUNKING_ENDPOINT, json={ "docs": docs_batch })
            end_late_chunking_time = datetime.datetime.now()
            total_late_chunking_duration += (end_late_chunking_time - start_late_chunking_time)
            logger.debug(f"[{file_db.id}] Chunk {i} late chunking completed.")

            if response.status_code == 200:
                # Step 5.2 - save each chunk of text and embedding to the vector database
                lc_docs = response.json()["docs"]
                final_chunk_number += len(lc_docs)
                final_chunk_size = len(lc_docs[0])

                start_ingestion_time = datetime.datetime.now()
                response = requests.post(INGESTION_ENDPOINT, json=response.json()) # pass the whole response from embedding to ingestion
                end_ingestion_time = datetime.datetime.now()
                total_ingestion_duration += (end_ingestion_time - start_ingestion_time)
                logger.debug(f"[{file_db.id}] Chunk {i} ingestion completed.")
                if response.status_code != 200:
                    file_db.status = 'error'
                    file_db.job_message = f"Error encountered while ingestion. {response_err(response)}"
                    file_db.late_chunking_end = datetime.datetime.now()
                    self.safe_commit()
                    raise Exception(f"Error encountered while ingestion. {response_err(response)}")
            else:
                file_db.status = 'error'
                file_db.job_message = f"Error encountered while late_chunking. {response_err(response)}"
                file_db.late_chunking_end = datetime.datetime.now()
                self.safe_commit()
                raise Exception(f"Error encountered while late chunking. {response_err(response)}")

            # Update the pipeline progress
            file_db.chunks_processed = i + len(docs_batch)
            file_db.late_chunking_end = file_db.late_chunking_start + total_late_chunking_duration
            file_db.ingestion_start = file_db.late_chunking_end
            file_db.ingestion_end = file_db.late_chunking_end + total_ingestion_duration
            self.safe_commit()

        file_db.chunk_size = final_chunk_size
        file_db.chunks_total = final_chunk_number
        file_db.chunks_processed = final_chunk_number
        self.safe_commit()
    else:
        batch_size = int(os.getenv('BATCH_SIZE', '32'))                    # max documents per embedding batch
        max_workers = int(os.getenv('MAX_NEW_WORKERS', '8'))               # max parallel embedding threads
        embedding_timeout_seconds = float(os.getenv('EMBEDDING_REQUEST_TIMEOUT_SECONDS', os.getenv('EMBEDDING_TIMEOUT_SECONDS', '120')))  # per-request embedding timeout (seconds)
        ingestion_timeout_seconds = 120.0                                   # per-request ingestion timeout (seconds)
        high_watermark_ratio = 0.5                                          # fraction of timeout above which load is reduced
        low_watermark_ratio = 0.3                                           # fraction of timeout below which load is increased
        latency_ema_alpha = 0.3                                             # EMA smoothing factor for embedding latency (higher = more reactive)
        max_batch_reduction_ratio = 0.25                                    # max single-step batch size reduction as fraction of current
        max_inflight_reduction_ratio = 0.25                                 # max single-step inflight count reduction as fraction of current
        min_batch_size = max(1, batch_size // 4)                            # floor for batch size adaptation
        max_batch_size = batch_size                                          # ceiling for batch size adaptation
        initial_batch_size = max(min_batch_size, max_batch_size // 2)       # starting batch size before warm-up ramp
        target_inflight = max(1, max_workers // 3)                          # initial number of concurrent inflight batches
        stabilization_window = target_inflight                               # batches to wait after an adaptation before allowing the next
        batches_since_last_change = 0                                        # counter of batches processed since last adaptation step

        file_db.embedding_start = datetime.datetime.now()
        file_db.ingestion_start = file_db.embedding_start
        file_db.status = 'embedding'
        file_db.job_message = 'Data embedding and ingestion in progress.'
        self.safe_commit()

        pipeline_start = datetime.datetime.now()   # wall-clock start of the entire embedding+ingestion pipeline
        error_occurred = None                       # set to error string by the first failing thread
        error_lock = Lock()                         # protects error_occurred from concurrent writes
        chunks_processed = 0                        # total documents successfully embedded and ingested
        chunks_lock = Lock()                        # protects chunks_processed from concurrent writes
        total_ingestion_time = datetime.timedelta() # cumulative ingestion time across all batches

        total_docs = len(dataprep_docs)                                              # total documents to process
        startup_batch_size = max(1, initial_batch_size // 3)                         # reduced batch size used during startup warm-up
        current_batch_size = max(min_batch_size, min(max_batch_size, startup_batch_size))  # active batch size (adapts at runtime)
        embedding_latency_ema = None                                                 # running EMA of embedding latency; None until first batch completes
        consecutive_fast_windows = 0                                                 # counter of consecutive batches below low_watermark (triggers scale-up)
        submitted_batches = 0                                                        # total batches submitted to the executor (used as batch ID)

        # Cache the ID so worker threads never touch the ORM object / session
        file_id = file_db.id

        logger.info(f"[{file_id}] Starting adaptive parallel pipeline: "
                    f"total_docs={total_docs}, startup_batch_size={current_batch_size}, "
                    f"max_workers={max_workers}, startup_inflight={target_inflight}, "
                    f"stabilization_window={stabilization_window}, timeout={embedding_timeout_seconds}s")

        def process_batch(batch_info):
            nonlocal chunks_processed, error_occurred, total_ingestion_time

            batch_num, docs_batch = batch_info

            with error_lock:
                if error_occurred:
                    logger.warning(f"[{file_id}] Batch {batch_num} skipped - another thread failed: {error_occurred}")
                    return None

            try:
                start_embedding = datetime.datetime.now()
                embed_response = requests.post(
                    EMBEDDING_ENDPOINT,
                    json={"docs": docs_batch},
                    timeout=embedding_timeout_seconds
                )
                embedding_time = datetime.datetime.now() - start_embedding

                if embed_response.status_code != 200:
                    raise Exception(f"Embedding failed for batch {batch_num}: {response_err(embed_response)}")

                logger.info(f"[{file_id}] Batch {batch_num} embedded in {embedding_time.total_seconds():.2f}s")

                start_ingestion = datetime.datetime.now()
                ingest_response = requests.post(
                    INGESTION_ENDPOINT,
                    json=embed_response.json(),
                    timeout=ingestion_timeout_seconds
                )
                ingestion_time = datetime.datetime.now() - start_ingestion

                if ingest_response.status_code != 200:
                    raise Exception(f"Ingestion failed for batch {batch_num}: {response_err(ingest_response)}")

                logger.info(f"[{file_id}] Batch {batch_num} ingested in {ingestion_time.total_seconds():.2f}s")

                with chunks_lock:
                    chunks_processed += len(docs_batch)
                    total_ingestion_time += ingestion_time

                return (batch_num, len(docs_batch), embedding_time.total_seconds())

            except Exception as e:
                with error_lock:
                    if error_occurred is None:
                        error_occurred = str(e)
                logger.error(f"[{file_id}] Batch {batch_num} failed: {str(e)}")
                raise Exception(f"Error encountered while processing, error={str(e)}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            next_doc_idx = 0
            completed = 0
            while next_doc_idx < total_docs or futures:
                while next_doc_idx < total_docs and len(futures) < target_inflight:
                    batch_end_idx = min(total_docs, next_doc_idx + current_batch_size)
                    docs_batch = dataprep_docs[next_doc_idx:batch_end_idx]
                    submitted_batches += 1
                    batch_num = submitted_batches
                    future = executor.submit(process_batch, (batch_num, docs_batch))
                    futures[future] = batch_num
                    next_doc_idx = batch_end_idx

                if not futures:
                    continue

                done_futures, _ = concurrent.futures.wait(
                    futures,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                    timeout=1
                )

                if not done_futures:
                    continue

                for future in done_futures:
                    batch_num = futures.pop(future)
                    try:
                        result = future.result()
                        if result is None:
                            continue

                        completed += 1
                        _, batch_len, embedding_latency_seconds = result

                        if embedding_latency_ema is None:
                            embedding_latency_ema = embedding_latency_seconds
                        else:
                            embedding_latency_ema = (
                                (latency_ema_alpha * embedding_latency_seconds)
                                + ((1 - latency_ema_alpha) * embedding_latency_ema)
                            )

                        batches_since_last_change += 1

                        high_threshold = embedding_timeout_seconds * high_watermark_ratio
                        low_threshold = embedding_timeout_seconds * low_watermark_ratio

                        if batches_since_last_change < stabilization_window:
                            pass  # still in stabilization window, skip adaptation
                        elif embedding_latency_ema > high_threshold:
                            consecutive_fast_windows = 0
                            prev_batch_size = current_batch_size
                            prev_target_inflight = target_inflight
                            reduced_batch_size = max(min_batch_size, current_batch_size // 2)  # halve batch size on backoff
                            max_batch_drop = max(1, int(prev_batch_size * max_batch_reduction_ratio))
                            min_batch_after_step = max(min_batch_size, prev_batch_size - max_batch_drop)
                            current_batch_size = max(reduced_batch_size, min_batch_after_step)

                            reduced_target_inflight = max(1, target_inflight // 2)  # halve inflight count on backoff
                            max_inflight_drop = max(1, int(prev_target_inflight * max_inflight_reduction_ratio))
                            min_inflight_after_step = max(1, prev_target_inflight - max_inflight_drop)
                            target_inflight = max(reduced_target_inflight, min_inflight_after_step)
                            if prev_batch_size != current_batch_size or prev_target_inflight != target_inflight:
                                batches_since_last_change = 0
                                stabilization_window = target_inflight
                                logger.warning(
                                    f"[{file_id}] Reducing load after batch {batch_num}: "
                                    f"latency_ema={embedding_latency_ema:.2f}s, "
                                    f"batch_size {prev_batch_size}->{current_batch_size}, "
                                    f"inflight {prev_target_inflight}->{target_inflight}"
                                )
                        elif embedding_latency_ema < low_threshold:
                            consecutive_fast_windows += 1
                            if consecutive_fast_windows >= 2:
                                prev_batch_size = current_batch_size
                                prev_target_inflight = target_inflight
                                current_batch_size = min(max_batch_size, current_batch_size + max(1, current_batch_size // 4))
                                target_inflight = min(max_workers, target_inflight + max(1, target_inflight // 4))
                                consecutive_fast_windows = 0
                                if prev_batch_size != current_batch_size or prev_target_inflight != target_inflight:
                                    batches_since_last_change = 0
                                    stabilization_window = target_inflight
                                    logger.info(
                                        f"[{file_id}] Increasing load after batch {batch_num}: "
                                        f"latency_ema={embedding_latency_ema:.2f}s, "
                                        f"batch_size {prev_batch_size}->{current_batch_size}, "
                                        f"inflight {prev_target_inflight}->{target_inflight}"
                                    )
                        else:
                            consecutive_fast_windows = 0

                        current_time = datetime.datetime.now()
                        file_db.chunks_processed = chunks_processed
                        file_db.embedding_end = current_time
                        file_db.ingestion_end = file_db.ingestion_start + total_ingestion_time
                        file_db.job_message = (
                            f'Processing: {chunks_processed}/{total_docs} chunks '
                            f'({completed} batches, batch_size={current_batch_size}, inflight={target_inflight})'
                        )
                        self.safe_commit()

                        if completed % 10 == 0 or chunks_processed == total_docs:
                            logger.info(
                                f"[{file_id}] Progress: completed_batches={completed}, "
                                f"chunks={chunks_processed}/{total_docs}, "
                                f"latency_ema={embedding_latency_ema:.2f}s"
                            )
                    except Exception as e:
                        for f in futures:
                            f.cancel()

                        file_db.status = 'error'
                        file_db.job_message = f"Error during processing: {str(e)}"
                        file_db.embedding_end = datetime.datetime.now()
                        self.safe_commit()
                        raise Exception(f"Error encountered while processing, error={str(e)}")

        pipeline_end = datetime.datetime.now()
        total_wall_time = pipeline_end - pipeline_start

        file_db.chunks_processed = chunks_processed
        file_db.embedding_end = pipeline_end
        file_db.ingestion_start = file_db.embedding_start
        file_db.ingestion_end = file_db.ingestion_start + total_ingestion_time
        self.safe_commit()

        logger.info(f"[{file_id}] Pipeline complete! "
                   f"Wall time: {total_wall_time.total_seconds():.2f}s, "
                   f"Total ingestion time: {total_ingestion_time.total_seconds():.2f}s, "
                   f"Batches: {completed}, "
                   f"Throughput: {chunks_processed / max(total_wall_time.total_seconds(), 0.001):.1f} docs/s")

    # Update the processing time
    file_db.status = 'ingested'
    file_db.job_message = 'Data ingestion completed.'
    file_db.embedding_model = EMBEDDING_MODEL_NAME
    file_db.task_id = ""
    self.safe_commit()
    logger.debug(f"[{file_db.id}] File stored successfully with embedding model: {EMBEDDING_MODEL_NAME}")
    return True


@shared_task(base=WithEDPTask, bind=True)
def delete_file_task(self, file_id: Any, *args, delete_from_sp: bool = True, **kwargs):
    file_db = self.db.query(FileStatus).filter(FileStatus.id == file_id).first()
    if file_db is None:
        raise Exception(f"File with id {file_id} not found")

    logger.debug(f"[{file_db.id}] Started processing file deletion.")

    # Step 1 - Delete everything related to the file in the vector database
    try:
        response = requests.post(f"{INGESTION_ENDPOINT}/delete", json={ 'file_id': str(file_db.id).replace('-', '') })
    except requests.exceptions.ConnectionError as e:
        file_db.status = 'error'
        file_db.marked_for_deletion = False
        file_db.job_message = f"Connection error while calling ingestion service during deletion (service may have restarted). {e}"
        self.safe_commit()
        raise Exception(f"Connection error while calling ingestion service during deletion. {e}")
    except Exception as e:
        file_db.status = 'error'
        file_db.marked_for_deletion = False
        file_db.job_message = f"Unexpected error while calling ingestion service during deletion. {e}"
        self.safe_commit()
        raise
    # 404 means no vector DB data found for this file, which can happen when the file
    # errored during ingestion. Proceed with DB cleanup.
    if response.status_code not in (200, 404):
        file_db.status = 'error'
        file_db.marked_for_deletion = False
        file_db.job_message = f"Error encountered while removing existing data related to file. {response_err(response)}"
        self.safe_commit()
        raise Exception(f"Error encountered while data clean up. {response_err(response)}")
    logger.debug(f"[{file_db.id}] Deleted existing data related to file (ingestion status: {response.status_code}).")

    # Step 1.5 - If the file came from SharePoint and this is a real deletion
    # (not a re-ingestion/update), delete it from the SP site too.
    if file_db.site_name and delete_from_sp:
        from app.sharepoint import delete_sp_file_by_path
        from app.models import SharePointSiteRecord
        from sqlalchemy import or_
        sp_record = self.db.query(SharePointSiteRecord).filter(
            or_(
                SharePointSiteRecord.display_name == file_db.site_name,
                SharePointSiteRecord.name == file_db.site_name,
            )
        ).first()
        if sp_record:
            try:
                asyncio.run(delete_sp_file_by_path(sp_record.graph_site_id, file_db.object_name))
                logger.info(f"[{file_db.id}] Deleted file from SharePoint site '{file_db.site_name}'.")
            except Exception as e:
                logger.warning(f"[{file_db.id}] Failed to delete from SharePoint site: {e}")
        else:
            logger.warning(f"[{file_db.id}] SP site record not found for '{file_db.site_name}', skipping SP delete.")

    # Step 2 - Delete the file from database
    id = file_db.id
    self.db.delete(file_db)
    self.safe_commit()
    logger.debug(f"[{id}] File deleted successfully from database.")
    return True


@shared_task(base=WithEDPTask, bind=True)
def process_link_task(self, link_id: Any, *args, **kwargs):
    link_db = self.db.query(LinkStatus).filter(LinkStatus.id == link_id).first()
    if link_db is None:
        raise Exception(f"Link with id {link_id} not found")

    if link_db.marked_for_deletion is True:
        logger.info(f"[{link_db.id}] Link is marked for deletion, skipping processing.")
        return False

    logger.debug(f"[{link_db.id}] Started processing link.")

    link_db.status = 'processing'
    link_db.job_message = 'Data clean up in progress.'
    self.safe_commit()

    # Step 0 - Delete everything related to the file in the vector database
    response = requests.post(f"{INGESTION_ENDPOINT}/delete", json={ 'link_id': str(link_db.id) })
    if response.status_code != 200:
        link_db.status = 'error'
        link_db.job_message = f"Error encountered while removing existing data related to file. {response_err(response)}"
        self.safe_commit()
        raise Exception(f"Error encountered while data clean up. {response_err(response)}")
    logger.debug(f"[{link_db.id}] Deleted existing data related to link.")

    # Step 1 - Prepare the file for text_extractor request
    link_db.text_extractor_start = datetime.datetime.now()
    link_db.status = 'text_extracting'
    link_db.job_message = 'Data loading in progress.'
    self.safe_commit()

    # Step 2 - Call the text_extractor service
    http = _keepalive_session()  # TCP keep-alive prevents IPVS from dropping the idle connection during long extractions
    dataprep_docs = []
    if HIERARCHICAL_DATAPREP_ENDPOINT is not None and HIERARCHICAL_DATAPREP_ENDPOINT != "":
        logger.info(f"[{link_db.id}] Hierarchical Dataprep endpoint is set. Using it for dataprep.")
        try:
            with self.db_keepalive():
                response = http.post(HIERARCHICAL_DATAPREP_ENDPOINT, json={ 'links': [link_db.uri] }, timeout=TEXT_EXTRACTOR_TIMEOUT_SECONDS)
        except requests.exceptions.ConnectionError as e:
            link_db.status = 'error'
            link_db.job_message = f"Connection error while calling hierarchical dataprep service (service may have restarted). {e}"
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Connection error while calling hierarchical dataprep service. {e}")
        except Exception as e:
            link_db.status = 'error'
            link_db.job_message = f"Unexpected error while calling hierarchical dataprep service. {e}"
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise
        if response.status_code != 200:
            link_db.status = 'error'
            link_db.job_message = f"Error encountered while data preparation. {response_err(response)}"
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while data preparation. {response_err(response)}")
        logger.debug(f"[{link_db.id}] Data preparation completed.")

        try:
            dataprep_docs = response.json()['docs']
            if len(dataprep_docs) == 0:
                logger.debug(f"[{link_db.id}] Data preparation returned 0 chunks.")
                raise Exception('No text extracted from the file.')

            link_db.chunk_size = len(dataprep_docs[0]) # Update chunk size
            link_db.chunks_total = len(dataprep_docs) # Update chunks count
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
        except Exception as e:
            link_db.status = 'error'
            link_db.job_message = 'No text extracted from the link.'
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error parsing response from data preparation service. {e} {response.text}")
    else:
        try:
            with self.db_keepalive():
                response = http.post(TEXT_EXTRACTOR_ENDPOINT, json={ 'links': [link_db.uri] }, timeout=TEXT_EXTRACTOR_TIMEOUT_SECONDS)
        except requests.exceptions.ConnectionError as e:
            link_db.status = 'error'
            link_db.job_message = f"Connection error while calling text extractor service (service may have restarted). {e}"
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Connection error while calling text extractor service. {e}")
        except Exception as e:
            link_db.status = 'error'
            link_db.job_message = f"Unexpected error while calling text extractor service. {e}"
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise
        if response.status_code != 200:
            link_db.status = 'error'
            link_db.job_message = f"Error encountered while data loading. {response_err(response)}"
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while data loading. {response_err(response)}")
        logger.debug(f"[{link_db.id}] Data loading completed.")

        text_extractor_docs = []
        try:
            text_extractor_docs = response.json()['loaded_docs']
            if len(text_extractor_docs) == 0:
                logger.debug(f"[{link_db.id}] Data loading returned 0 documents.")
                raise Exception('No text extracted from the link.')
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
        except Exception as e:
            link_db.status = 'error'
            link_db.job_message = 'No text extracted from the link.'
            link_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error parsing response from data loading service. {e} {response.text}")

        # Step 3 - Call the text compression service to compress the documents
        link_db.text_compression_start = datetime.datetime.now()
        link_db.status = 'text_compression'
        link_db.job_message = 'Text compression in progress.'
        self.safe_commit()
        logger.info(f"[{link_db.id}] Starting text compression ({len(text_extractor_docs)} docs).")

        response = requests.post(TEXT_COMPRESSION_ENDPOINT, json={ 'loaded_docs': text_extractor_docs }, timeout=TEXT_PROCESSING_TIMEOUT_SECONDS)
        if response.status_code != 200:
            link_db.status = 'error'
            link_db.job_message = f"Error encountered while text compressing. {response_err(response)}"
            link_db.text_compression_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while text compressing. {response_err(response)}")
        logger.info(f"[{link_db.id}] Text compression completed.")

        dataprep_compressed_docs = []
        try:
            dataprep_compressed_docs = response.json()['loaded_docs']
            if len(dataprep_compressed_docs) == 0:
                logger.debug(f"[{link_db.id}] Text compression returned 0 documents.")
                raise Exception('No text compressed.')
            link_db.chunk_size = len(dataprep_compressed_docs[0]) # Update chunk size
            link_db.chunks_total = len(dataprep_compressed_docs) # Update chunks count
            link_db.text_compression_end = datetime.datetime.now()
            self.safe_commit()
        except Exception as e:
            link_db.status = 'error'
            link_db.job_message = 'No text compressed.'
            link_db.text_compression_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error parsing response from text compression service. {e} {response.text}")

        # Step 4 - Call the data splitter service to split the documents into smaller chunks
        link_db.text_splitter_start = datetime.datetime.now()
        link_db.status = 'text_splitting'
        link_db.job_message = 'Data splitting in progress.'
        self.safe_commit()
        logger.info(f"[{link_db.id}] Starting text splitting ({len(dataprep_compressed_docs)} docs).")

        response = requests.post(TEXT_SPLITTER_ENDPOINT, json={ 'loaded_docs': dataprep_compressed_docs }, timeout=TEXT_PROCESSING_TIMEOUT_SECONDS)
        if response.status_code != 200:
            link_db.status = 'error'
            link_db.job_message = f"Error encountered while data splitting. {response_err(response)}"
            link_db.text_splitter_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while data splitting. {response_err(response)}")
        logger.info(f"[{link_db.id}] Data splitting completed.")

        dataprep_docs = []
        try:
            dataprep_docs = response.json()['docs']
            if len(dataprep_docs) == 0:
                logger.debug(f"[{link_db.id}] Data splitting returned 0 chunks.")
                raise Exception('No text extracted from the file.')
            link_db.chunk_size = len(dataprep_docs[0]) # Update chunk size
            link_db.chunks_total = len(dataprep_docs) # Update chunks count
            link_db.text_splitter_end = datetime.datetime.now()
            self.safe_commit()
        except Exception as e:
            link_db.status = 'error'
            link_db.job_message = 'No text extracted from the file.'
            link_db.text_splitter_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error parsing response from data splitting service. {e} {response.text}")

    # 4.1 Update the metadata info from database
    for doc in dataprep_docs:
        doc['metadata']['link_id'] = str(link_db.id).replace('-', '') # uuid w/o hyphens because redis does not support search with hypens

    # Step 4.5 (Optional) - scan datapreped documents with Dataprep Guardrail
    dpguard_msg = ""
    dpguard_status = ""
    try:
        dpguard_enabled = os.getenv('DPGUARD_ENABLED', "false")
        logger.info(f"dpguard_enabled: {dpguard_enabled}")
        if dpguard_enabled == "true":
            link_db.dpguard_start = datetime.datetime.now()
            link_db.status = 'dpguard'
            link_db.job_message = 'Data Preparation Guardrail in progress.'
            self.safe_commit()
            dpguard_endpoint = os.environ.get('DPGUARD_ENDPOINT')
            logger.info(f"dpguard_endpoint: {dpguard_endpoint}")
            logger.info("Dataprep Guardrail enabled. Scanning the documents.")
            response = requests.post(dpguard_endpoint, json={ 'docs': dataprep_docs })
            if response.status_code != 200:
                dpguard_msg = 'Dataprep Guardrail failed.'
                dpguard_status = 'error'
                if response.status_code == 466:
                    dpguard_msg = "Dataprep Guardrail blocked embedding this document"
                    dpguard_status = 'blocked'
                raise Exception(f"{dpguard_msg} {response_err(response)}")
            link_db.dpguard_end = datetime.datetime.now()
            self.safe_commit()
            logger.info("Dataprep Guardrail completed.")
    except Exception as e:
        link_db.job_message = dpguard_msg if dpguard_msg else 'Error while executing dataprep guardrail.'
        link_db.status = dpguard_status if dpguard_status else 'error'
        link_db.dpguard_end = datetime.datetime.now()
        self.safe_commit()
        raise Exception(f"Error while executing dataprep guardrail. {e} {response.text}")

    # Step 5 - Call the embedding service and ingestion service in batches
    batch_size = int(os.getenv('BATCH_SIZE', '128'))                    # max documents per embedding batch
    embedding_timeout_seconds = float(os.getenv('EMBEDDING_REQUEST_TIMEOUT_SECONDS', '120'))  # per-request embedding timeout (seconds)
    ingestion_timeout_seconds = 120.0                                   # per-request ingestion timeout (seconds)
    high_watermark_ratio = 0.5                                          # fraction of timeout above which load is reduced
    low_watermark_ratio = 0.3                                           # fraction of timeout below which load is increased
    max_batch_reduction_ratio = 0.25                                    # max single-step batch size reduction as fraction of current
    min_batch_size = max(1, batch_size // 4)                            # floor for batch size adaptation
    max_batch_size = batch_size                                          # ceiling for batch size adaptation
    link_db.embedding_start = datetime.datetime.now()
    link_db.ingestion_start = link_db.embedding_start
    link_db.status = 'embedding'
    link_db.job_message = 'Data embedding in progress.'
    self.safe_commit()
    total_embedding_duration = datetime.timedelta()
    total_ingestion_duration = datetime.timedelta()
    initial_batch_size = max(min_batch_size, max_batch_size // 2)       # starting batch size before warm-up ramp
    startup_batch_size = max(1, initial_batch_size // 3)                # reduced batch size used during startup warm-up
    current_batch_size = max(min_batch_size, min(max_batch_size, startup_batch_size))  # active batch size (adapts at runtime)
    latency_ema_alpha = 0.3                                             # EMA smoothing factor for embedding latency (higher = more reactive)
    embedding_latency_ema = None                                        # running EMA of embedding latency; None until first batch completes
    consecutive_fast_windows = 0                                        # counter of consecutive batches below low_watermark (triggers scale-up)
    i = 0                                                               # current document offset in dataprep_docs
    while i < len(dataprep_docs):
        docs_batch = dataprep_docs[i:i+current_batch_size]

        start_embedding_time = datetime.datetime.now()
        response = requests.post(
            EMBEDDING_ENDPOINT,
            json={"docs": docs_batch},
            timeout=embedding_timeout_seconds
        )
        end_embedding_time = datetime.datetime.now()
        embedding_duration = (end_embedding_time - start_embedding_time)
        total_embedding_duration += embedding_duration

        embedding_latency_seconds = embedding_duration.total_seconds()
        if embedding_latency_ema is None:
            embedding_latency_ema = embedding_latency_seconds
        else:
            embedding_latency_ema = (
                (latency_ema_alpha * embedding_latency_seconds)
                + ((1 - latency_ema_alpha) * embedding_latency_ema)
            )

        high_threshold = embedding_timeout_seconds * high_watermark_ratio
        low_threshold = embedding_timeout_seconds * low_watermark_ratio

        if embedding_latency_ema > high_threshold:
            consecutive_fast_windows = 0
            prev_batch_size = current_batch_size
            reduced_batch_size = max(min_batch_size, current_batch_size // 2)  # halve batch size on backoff
            max_batch_drop = max(1, int(prev_batch_size * max_batch_reduction_ratio))
            min_batch_after_step = max(min_batch_size, prev_batch_size - max_batch_drop)
            current_batch_size = max(reduced_batch_size, min_batch_after_step)
            if prev_batch_size != current_batch_size:
                logger.warning(
                    f"[{link_db.id}] Reducing batch size: "
                    f"latency_ema={embedding_latency_ema:.2f}s, "
                    f"batch_size {prev_batch_size}->{current_batch_size}"
                )
        elif embedding_latency_ema < low_threshold:
            consecutive_fast_windows += 1
            if consecutive_fast_windows >= 2:
                prev_batch_size = current_batch_size
                current_batch_size = min(max_batch_size, current_batch_size + max(1, current_batch_size // 4))
                consecutive_fast_windows = 0
                if prev_batch_size != current_batch_size:
                    logger.info(
                        f"[{link_db.id}] Increasing batch size: "
                        f"latency_ema={embedding_latency_ema:.2f}s, "
                        f"batch_size {prev_batch_size}->{current_batch_size}"
                    )
        else:
            consecutive_fast_windows = 0

        logger.debug(f"[{link_db.id}] Chunk offset {i} embedding completed.")
        if response.status_code == 200:
            start_ingestion_time = datetime.datetime.now()
            response = requests.post(
                INGESTION_ENDPOINT,
                json=response.json(),
                timeout=ingestion_timeout_seconds
            )
            end_ingestion_time = datetime.datetime.now()
            total_ingestion_duration += (end_ingestion_time - start_ingestion_time)
            logger.debug(f"[{link_db.id}] Chunk offset {i} ingestion completed.")
            if response.status_code != 200:
                link_db.status = 'error'
                link_db.job_message = f"Error encountered while ingestion. {response_err(response)}"
                link_db.embedding_end = datetime.datetime.now()
                self.safe_commit()
                raise Exception(f"Error encountered while ingestion. {response_err(response)}")
        else:
            link_db.status = 'error'
            link_db.job_message = f"Error encountered while embedding. {response_err(response)}"
            link_db.embedding_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while embedding. {response_err(response)}")

        link_db.chunks_processed = i + len(docs_batch)
        link_db.embedding_end = link_db.embedding_start + total_embedding_duration
        link_db.ingestion_start = link_db.embedding_end
        link_db.ingestion_end = link_db.embedding_end + total_ingestion_duration
        self.safe_commit()
        i += len(docs_batch)

    # Update the processing time
    link_db.status = 'ingested'
    link_db.job_message = 'Data ingestion completed.'
    link_db.embedding_model = EMBEDDING_MODEL_NAME
    link_db.task_id = ""
    self.safe_commit()
    logger.debug(f"[{link_db.id}] Link stored successfully with embedding model: {EMBEDDING_MODEL_NAME}")
    return True


@shared_task(base=WithEDPTask, bind=True)
def delete_link_task(self, link_id: Any, *args, **kwargs):
    link_db = self.db.query(LinkStatus).filter(LinkStatus.id == link_id).first()
    if link_db is None:
        raise Exception(f"Link with id {link_id} not found")

    logger.debug(f"[{link_db.id}] Started processing file deletion.")

    # Step 1 - Delete everything related to the file in the vector database
    response = requests.post(f"{INGESTION_ENDPOINT}/delete", json={ 'link_id': str(link_db.id).replace('-', '') })
    logger.debug(f"[{link_db.id}] Deleted existing data related to file.")
    if response.status_code != 200:
        link_db.job_status = 'error'
        link_db.job_message = f"Error encountered while removing existing data related to file. {response_err(response)}"
        self.safe_commit()
        raise Exception(f"Error encountered while data clean up. {response_err(response)}")

    # Step 2 - Delete the file from database
    id = link_db.id
    self.db.delete(link_db)
    self.safe_commit()
    logger.debug(f"[{id}] File deleted successfully from database.")
    return True


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    edp_sync_seconds = os.environ.get('EDP_SYNC_TASK_TIME_SECONDS', None)
    if edp_sync_seconds and edp_sync_seconds != "":
        logger.info(f"Adding periodic sync task each {edp_sync_seconds} seconds")
        sender.add_periodic_task(int(edp_sync_seconds), sync_files_task.s(), name='Sync files between storage and db')
    else:
        logger.info("No periodic S3 sync task registered")

    sp_sync_seconds = os.environ.get('EDP_SP_SYNC_TASK_TIME_SECONDS', None)
    if sp_sync_seconds and sp_sync_seconds != "":
        logger.info(f"Adding periodic SharePoint sync task each {sp_sync_seconds} seconds")
        sender.add_periodic_task(int(sp_sync_seconds), sync_sharepoint_task.s(), name='Sync SharePoint files')
    else:
        logger.info("No periodic SharePoint sync task registered")

@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 1})
def sync_files_task(self, *Args, **kwargs):
    from app.main import add_new_file, delete_existing_file, sync_files, minio_internal

    logger.debug("Started File Sync process")

    def _sync_add(bucket_name, object_name, etag, content_type, size):
        add_new_file(object_name, etag, content_type, size, bucket_name=bucket_name)

    def _sync_delete(bucket_name, object_name):
        delete_existing_file(object_name, bucket_name=bucket_name)

    try:
        sync_files(minio_internal, _sync_add, _sync_add, _sync_delete)
    except Exception as e:
        logger.error(f"Error syncing files: {e}")

    logger.debug("Ended File Sync process")
    return True


@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 1})
def sync_sharepoint_task(self, *Args, **kwargs):
    from app.main import add_new_file
    from app.sharepoint import sharepoint_enabled, build_sharepoint_sync_plan, delete_sp_file, sp_sync_lock

    if not sharepoint_enabled():
        logger.debug("SharePoint integration not configured, skipping sync")
        return True

    logger.debug("Started SharePoint Sync process")
    try:
        with sp_sync_lock(blocking=False) as acquired:
            if not acquired:
                logger.info("SharePoint sync lock is held by another process, skipping scheduled sync")
                return True

            async def _do_sync():
                actions, _ = await build_sharepoint_sync_plan()
                for action, sn, object_name, file_info, graph_site_id in actions:
                    if action in ('add', 'update'):
                        add_new_file(
                            object_name,
                            file_info.get('etag', ''),
                            file_info.get('content_type', 'application/octet-stream'),
                            file_info.get('size', 0),
                            site_name=sn,
                        )
                    elif action == 'delete':
                        delete_sp_file(sn, object_name)

            asyncio.run(_do_sync())
    except Exception as e:
        logger.error(f"Error syncing SharePoint files: {e}")

    logger.debug("Ended SharePoint Sync process")
    return True
