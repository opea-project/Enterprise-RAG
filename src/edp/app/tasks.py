# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Any
import requests
import base64
import datetime
from dotenv import load_dotenv
from minio.error import S3Error
from sqlalchemy import create_engine
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
    taks_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1
)

celery.conf.update(
    redis_backend_health_check_interval=10,
    redis_retry_on_timeout=True,
    redis_max_connections=10,
    redis_socket_timeout=30,
    redis_socket_keepalive=True
)

HIERARCHICAL_DATAPREP_ENDPOINT  = os.environ.get('HIERARCHICAL_DATAPREP_ENDPOINT')
TEXT_EXTRACTOR_ENDPOINT  = os.environ.get('TEXT_EXTRACTOR_ENDPOINT')
TEXT_COMPRESSION_ENDPOINT  = os.environ.get('TEXT_COMPRESSION_ENDPOINT')
TEXT_SPLITTER_ENDPOINT  = os.environ.get('TEXT_SPLITTER_ENDPOINT')
EMBEDDING_ENDPOINT = os.environ.get('EMBEDDING_ENDPOINT')
LATE_CHUNKING_ENDPOINT = os.environ.get('LATE_CHUNKING_ENDPOINT')
INGESTION_ENDPOINT = os.environ.get('INGESTION_ENDPOINT')

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
            self._engine = create_engine(DATABASE_URL, pool_size=8, max_overflow=8) # single class instance used for all task with concurrency

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

    def safe_commit(self):
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error committing to database: {e}")
            self.db.rollback()
            raise e

def response_err(response):
    try:
        return response.json().get('detail', response.text)
    except Exception:
        return response.text

@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def process_file_task(self, file_id: Any, *args, **kwargs):

    file_db = self.db.query(FileStatus).filter(FileStatus.id == file_id).first()
    if file_db is None:
        raise Exception(f"File with id {file_id} not found")

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
        minio_response = self.minio.get_object(bucket_name=file_db.bucket_name, object_name=file_db.object_name)
        file_data = minio_response.read()
        file_base64 = base64.b64encode(file_data).decode('ascii')
        logger.debug(f"[{file_db.id}] Retrieved file from S3 storage.")
    except S3Error as e:
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
    dataprep_docs = []
    if HIERARCHICAL_DATAPREP_ENDPOINT is not None and HIERARCHICAL_DATAPREP_ENDPOINT != "":
        logger.info(f"[{file_db.id}] Hierarchical Dataprep endpoint is set. Using it for dataprep.")
        response = requests.post(HIERARCHICAL_DATAPREP_ENDPOINT, json={ 'files': [{'filename': file_name, 'data64': file_base64}] })
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
        response = requests.post(TEXT_EXTRACTOR_ENDPOINT, json={ 'files': [{'filename': file_name, 'data64': file_base64}] })
        if response.status_code != 200:
            file_db.status = 'error'
            file_db.job_message = f"Error encountered while data loading. {response_err(response)}"
            file_db.text_extractor_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while data loading. {response_err(response)}")
        logger.debug(f"[{file_db.id}] Data loading completed.")

        text_extractor_docs = []
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

        response = requests.post(TEXT_COMPRESSION_ENDPOINT, json={ 'loaded_docs': text_extractor_docs })
        if response.status_code != 200:
            file_db.status = 'error'
            file_db.job_message = f"Error encountered while text compressing. {response_err(response)}"
            file_db.text_compression_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while text compressing. {response_err(response)}")
        logger.debug(f"[{file_db.id}] Text compression completed.")

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

        late_chunking_enabled = os.getenv('LATE_CHUNKING_ENABLED', "false").lower()
        additional_params = {}
        if late_chunking_enabled == "true":
            additional_params = { 'chunk_size': 8192, 'chunk_overlap': 1024 }
        
        response = requests.post(TEXT_SPLITTER_ENDPOINT, json={ 'loaded_docs': dataprep_compressed_docs, **additional_params })
        if response.status_code != 200:
            file_db.status = 'error'
            file_db.job_message = f"Error encountered while data splitting. {response_err(response)}"
            file_db.text_splitter_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while data splitting. {response_err(response)}")
        logger.debug(f"[{file_db.id}] Data splitting completed.")

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
        # Step 5 - Call the embedding service and ingestion service in batches
        # Optimized: Pipeline embedding and ingestion to maximize throughput
        # Strategy: 
        #   - Use smaller batches to reduce serialization/network overhead
        #   - Send multiple embedding requests in parallel to saturate vLLM
        #   - Ingest results in parallel as they complete
        import concurrent.futures
        from threading import Lock

        # Smaller batch size for faster HTTP transfers, parallel requests saturate vLLM
        batch_size = int(os.getenv('BATCH_SIZE', '32'))  # Smaller batches transfer faster
        max_workers = int(os.getenv('MAX_NEW_WORKERS', '8'))  # Maximum parallel workers for embedding and ingestion

        file_db.embedding_start = datetime.datetime.now()
        file_db.ingestion_start = file_db.embedding_start
        file_db.status = 'embedding'
        file_db.job_message = 'Data embedding and ingestion in progress.'
        self.safe_commit()

        # Track actual wall-clock time, not cumulative
        pipeline_start = datetime.datetime.now()
        error_occurred = None
        error_lock = Lock()
        chunks_processed = 0
        chunks_lock = Lock()
        total_ingestion_time = datetime.timedelta()  # Sum of all ingestion times

        total_batches = (len(dataprep_docs) + batch_size - 1) // batch_size
        total_docs = len(dataprep_docs)

        logger.info(f"[{file_db.id}] Starting parallel pipeline: {total_batches} batches, "
                   f"batch_size={batch_size}, max_workers={max_workers}")

        def process_batch(batch_info):
            """Process a single batch: embed then ingest"""
            nonlocal chunks_processed, error_occurred, total_ingestion_time

            batch_idx, docs_batch = batch_info
            batch_num = batch_idx + 1

            # Check if error occurred in another thread (fail-fast mechanism)
            # If any parallel worker fails, all others should stop immediately
            # looking for errors in embedding and ingestion steps
            with error_lock:
                if error_occurred:
                    logger.warning(f"[{file_db.id}] Batch {batch_num} skipped - another thread failed: {error_occurred}")
                    return None

            try:
                # Step 1: Embedding
                start_embedding = datetime.datetime.now()
                embed_response = requests.post(EMBEDDING_ENDPOINT, json={"docs": docs_batch})
                embedding_time = datetime.datetime.now() - start_embedding

                if embed_response.status_code != 200:
                    raise Exception(f"Embedding failed for batch {batch_num}: {response_err(embed_response)}")

                logger.info(f"[{file_db.id}] Batch {batch_num}/{total_batches} embedded in {embedding_time.total_seconds():.2f}s")

                # Step 2: Ingestion (immediately after embedding)
                start_ingestion = datetime.datetime.now()
                ingest_response = requests.post(INGESTION_ENDPOINT, json=embed_response.json())
                ingestion_time = datetime.datetime.now() - start_ingestion

                if ingest_response.status_code != 200:
                    raise Exception(f"Ingestion failed for batch {batch_num}: {response_err(ingest_response)}")

                logger.info(f"[{file_db.id}] Batch {batch_num}/{total_batches} ingested in {ingestion_time.total_seconds():.2f}s")

                # Update counters (thread-safe)
                with chunks_lock:
                    chunks_processed += len(docs_batch)
                    total_ingestion_time += ingestion_time

                return (batch_num, len(docs_batch))

            except Exception as e:
                with error_lock:
                    if error_occurred is None:
                        error_occurred = str(e)
                logger.error(f"[{file_db.id}] Batch {batch_num} failed: {str(e)}")
                raise Exception(f"Error encountered while processing, error={str(e)}")

        # Prepare all batches
        batches = []
        for batch_idx, i in enumerate(range(0, len(dataprep_docs), batch_size)):
            docs_batch = dataprep_docs[i:i+batch_size]
            batches.append((batch_idx, docs_batch))

        # Process batches with parallel workers
        # Each worker handles embed+ingest for its batch
        # This keeps both embedding service and ingestion service saturated

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_batch, batch): batch[0] for batch in batches}

            completed = 0
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        completed += 1
                        batch_num, batch_len = result

                        # Update database with progress after each batch completes
                        current_time = datetime.datetime.now()
                        file_db.chunks_processed = chunks_processed
                        file_db.embedding_end = current_time
                        file_db.ingestion_end = file_db.ingestion_start + total_ingestion_time
                        file_db.job_message = f'Processing: {chunks_processed}/{total_docs} chunks ({completed}/{total_batches} batches)'
                        self.safe_commit()

                        if completed % 10 == 0 or completed == total_batches:
                            logger.info(f"[{file_db.id}] Progress: {completed}/{total_batches} batches, "
                                       f"{chunks_processed}/{total_docs} chunks")
                except Exception as e:
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()

                    file_db.status = 'error'
                    file_db.job_message = f"Error during processing: {str(e)}"
                    file_db.embedding_end = datetime.datetime.now()
                    self.safe_commit()
                    raise Exception(f"Error encountered while processing, error={str(e)}")

        # Calculate actual wall-clock time (not cumulative)
        pipeline_end = datetime.datetime.now()
        total_wall_time = pipeline_end - pipeline_start

        # Update final stats
        # - embedding_end: wall-clock end time
        # - ingestion uses summed duration (since ingestions run in parallel)
        file_db.chunks_processed = chunks_processed
        file_db.embedding_end = pipeline_end
        file_db.ingestion_start = file_db.embedding_start  # They overlap in parallel execution
        file_db.ingestion_end = file_db.ingestion_start + total_ingestion_time  # Sum of all ingestion times
        self.safe_commit()

        logger.info(f"[{file_db.id}] Pipeline complete! "
                   f"Wall time: {total_wall_time.total_seconds():.2f}s, "
                   f"Total ingestion time: {total_ingestion_time.total_seconds():.2f}s, "
                   f"Batches: {total_batches}, "
                   f"Throughput: {chunks_processed / total_wall_time.total_seconds():.1f} docs/s")

    # Update the processing time
    file_db.status = 'ingested'
    file_db.job_message = 'Data ingestion completed.'
    file_db.task_id = ""
    self.safe_commit()
    logger.debug(f"[{file_db.id}] File stored successfully.")
    return True


@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def delete_file_task(self, file_id: Any, *args, **kwargs):
    file_db = self.db.query(FileStatus).filter(FileStatus.id == file_id).first()
    if file_db is None:
        raise Exception(f"File with id {file_id} not found")

    logger.debug(f"[{file_db.id}] Started processing file deletion.")

    # Step 1 - Delete everything related to the file in the vector database
    response = requests.post(f"{INGESTION_ENDPOINT}/delete", json={ 'file_id': str(file_db.id).replace('-', '') })
    logger.debug(f"[{file_db.id}] Deleted existing data related to file.")
    if response.status_code != 200:
        file_db.job_status = 'error'
        file_db.job_message = f"Error encountered while removing existing data related to file. {response_err(response)}"
        self.safe_commit()
        raise Exception(f"Error encountered while data clean up. {response_err(response)}")

    # Step 2 - Delete the file from database
    id = file_db.id
    self.db.delete(file_db)
    self.safe_commit()
    logger.debug(f"[{id}] File deleted successfully from database.")
    return True


@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def process_link_task(self, link_id: Any, *args, **kwargs):
    link_db = self.db.query(LinkStatus).filter(LinkStatus.id == link_id).first()
    if link_db is None:
        raise Exception(f"Link with id {link_db} not found")

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
    dataprep_docs = []
    if HIERARCHICAL_DATAPREP_ENDPOINT is not None and HIERARCHICAL_DATAPREP_ENDPOINT != "":
        logger.info(f"[{link_db.id}] Hierarchical Dataprep endpoint is set. Using it for dataprep.")
        response = requests.post(HIERARCHICAL_DATAPREP_ENDPOINT, json={ 'links': [link_db.uri] })
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
        response = requests.post(TEXT_EXTRACTOR_ENDPOINT, json={ 'links': [link_db.uri] })
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

        response = requests.post(TEXT_COMPRESSION_ENDPOINT, json={ 'loaded_docs': text_extractor_docs })
        if response.status_code != 200:
            link_db.status = 'error'
            link_db.job_message = f"Error encountered while text compressing. {response_err(response)}"
            link_db.text_compression_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while text compressing. {response_err(response)}")
        logger.debug(f"[{link_db.id}] Text compression completed.")

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

        response = requests.post(TEXT_SPLITTER_ENDPOINT, json={ 'loaded_docs': dataprep_compressed_docs })
        if response.status_code != 200:
            link_db.status = 'error'
            link_db.job_message = f"Error encountered while data splitting. {response_err(response)}"
            link_db.text_splitter_end = datetime.datetime.now()
            self.safe_commit()
            raise Exception(f"Error encountered while data splitting. {response_err(response)}")
        logger.debug(f"[{link_db.id}] Data splitting completed.")

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
    batch_size = int(os.getenv('BATCH_SIZE', '128'))
    link_db.embedding_start = datetime.datetime.now()
    link_db.ingestion_start = link_db.embedding_start
    link_db.status = 'embedding'
    link_db.job_message = 'Data embedding in progress.'
    self.safe_commit()
    total_embedding_duration = datetime.timedelta()
    total_ingestion_duration = datetime.timedelta()
    for i in range(0, len(dataprep_docs), batch_size):
        # Step 5.1 - send each chunk of text from dataprep to the embedding service
        docs_batch = dataprep_docs[i:i+batch_size]
        start_embedding_time = datetime.datetime.now()
        response = requests.post(EMBEDDING_ENDPOINT, json={ "docs": docs_batch })
        end_embedding_time = datetime.datetime.now()
        total_embedding_duration += (end_embedding_time - start_embedding_time)
        logger.debug(f"[{link_db.id}] Chunk {i} embedding completed.")
        if response.status_code == 200:
            # Step 5.2 - save each chunk of text and embedding to the vector database
            start_ingestion_time = datetime.datetime.now()
            response = requests.post(INGESTION_ENDPOINT, json=response.json()) # pass the whole response from embedding to ingestion
            end_ingestion_time = datetime.datetime.now()
            total_ingestion_duration += (end_ingestion_time - start_ingestion_time)
            logger.debug(f"[{link_db.id}] Chunk {i} ingestion completed.")
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

        # Update the pipeline progress
        link_db.chunks_processed = i + len(docs_batch)
        link_db.embedding_end = link_db.embedding_start + total_embedding_duration
        link_db.ingestion_start = link_db.embedding_end
        link_db.ingestion_end = link_db.embedding_end + total_ingestion_duration
        self.safe_commit()

    # Update the processing time
    link_db.status = 'ingested'
    link_db.job_message = 'Data ingestion completed.'
    link_db.task_id = ""
    self.safe_commit()
    logger.debug(f"[{link_db.id}] File stored successfully.")
    return True


@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
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
        logger.info("No periodic tasks registered")

@shared_task(base=WithEDPTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 1})
def sync_files_task(self, *Args, **kwargs):
    from app.main import add_new_file, delete_existing_file, sync_files, minio_internal

    logger.debug("Started File Sync process")

    try:
        sync_files(minio_internal, add_new_file, add_new_file, delete_existing_file)
    except Exception as e:
        logger.error(f"Error syncing files: {e}")

    logger.debug("Ended File Sync process")
    return True
