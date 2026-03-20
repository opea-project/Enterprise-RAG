# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
from concurrent.futures import ProcessPoolExecutor
import os
import time
import base64
import io
import uuid
import requests
import pymupdf

from pathlib import Path
from urllib3.exceptions import MaxRetryError
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException
from pathvalidate import is_valid_filename

from utils.opea_text_extractor import OPEATextExtractor
from comps.text_extractor.utils.file_loaders.load_pdf import _process_single_page_from_file
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceType
from comps.cores.proto.docarray import DataPrepInput, TextDoc, TextSplitterInput
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.mega.base_statistics import register_statistics, statistics_dict
from requests.exceptions import HTTPError, ConnectionError, ProxyError

# Define the unique service name for the microservice
USVC_NAME='opea_service@opea_text_extractor'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Load ASR endpoint configuration
ASR_MODEL_SERVER_ENDPOINT = os.getenv('ASR_MODEL_SERVER_ENDPOINT')
def validate_asr_endpoint(asr_endpoint):
    """Validate that the ASR endpoint is responsive."""
    if not asr_endpoint or asr_endpoint.strip() == "":
        logger.info("ASR_MODEL_SERVER_ENDPOINT is not configured. Audio file support will be disabled.")
        return

    try:
        url = f"{asr_endpoint.rstrip('/')}/v1/health_check"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logger.info(f"ASR endpoint validation successful: {asr_endpoint}")
    except Exception as e:
        logger.error(f"Unexpected error validating ASR endpoint: {asr_endpoint}. Error: {str(e)}")
        raise

# These functions are top-level (picklable) so Python's multiprocessing can submit them
# to the shared ProcessPoolExecutor. Each handles one unit of work:
#   - run_single_file: one non-PDF file
#   - run_single_link: one URL
# PDF pages are submitted via _process_single_page_from_file (imported from load_pdf).
# This design gives the shared pool all work at page granularity — no nested pools.
def run_single_file(filename: str, file_bytes: bytes, asr_endpoint):
    """Process a single non-PDF file in a pool worker. Accepts raw bytes to stay picklable."""
    binary_file = io.BytesIO(file_bytes)
    upload_file = UploadFile(filename=filename, file=binary_file)
    text_extractor = OPEATextExtractor(asr_endpoint=asr_endpoint)
    return text_extractor._load_files([upload_file])


def run_single_link(link: str, asr_endpoint):
    """Process a single link in a pool worker."""
    text_extractor = OPEATextExtractor(asr_endpoint=asr_endpoint)
    return text_extractor._load_links([link])


# Process Pool Executor was introduced due to API being unresponsive while computing non-io tasks.
# Originally, async functions are run in event loop which means that they block the server thread
# thus making it unresponsive for other requests - mainly health_check - which then might cause
# some issues on k8s deployments, showing the pod as not ready by failing the liveness probe.
# While moving it to sync function fixed that issue this meant that it would run in a separate
# thread but was instead slower due to not using async io calls. The resolution is to run it
# as an async function for io improvement, but spawn a separate process for heavy CPU usage calls.
# https://github.com/fastapi/fastapi/issues/3725#issuecomment-902629033
# https://luis-sena.medium.com/how-to-optimize-fastapi-for-ml-model-serving-6f75fb9e040d

# TEXT_EXTRACTOR_MAX_WORKERS is injected by the Kubernetes Downward API (limits.cpu)
# in the pod spec, so this always reflects the actual pod CPU limit.
_max_workers = int(os.getenv('TEXT_EXTRACTOR_MAX_WORKERS', 4))
pool = ProcessPoolExecutor(max_workers=_max_workers)
logger.info(f"ProcessPoolExecutor initialized with max_workers={_max_workers} (set TEXT_EXTRACTOR_MAX_WORKERS to override)")


async def _process_pdf_windowed(pdf_path: str, filename: str, page_count: int, metadata: dict) -> TextDoc:
    """
    Process all pages of a PDF using a sliding window of at most _max_workers
    concurrent pool tasks.

    Why windowed instead of submitting all pages upfront:
    - ProcessPoolExecutor has a FIFO queue. Submitting all N pages at once fills
      the queue, starving later-arriving requests until this file is done.
    - By keeping only _max_workers tasks in-flight at once and awaiting
      FIRST_COMPLETED before submitting the next page, we yield to the asyncio
      event loop after each completion. This lets other concurrent requests'
      _process_pdf_windowed coroutines also submit their next pages.
    - Result: pages from all concurrent requests interleave naturally in the pool.
    """
    loop = asyncio.get_event_loop()
    results: list = [None] * page_count
    inflight: dict = {}  # task -> page_num
    next_page = 0
    completed = 0
    start_time = time.time()

    try:
        while next_page < page_count or inflight:
            # Fill window up to _max_workers in-flight tasks
            while next_page < page_count and len(inflight) < _max_workers:
                page_num = next_page
                fut = loop.run_in_executor(pool, _process_single_page_from_file, pdf_path, page_num)
                task = asyncio.ensure_future(fut)
                inflight[task] = page_num
                next_page += 1

            # Wait for at least one to finish, then yield so other requests can submit
            done, _ = await asyncio.wait(set(inflight.keys()), return_when=asyncio.FIRST_COMPLETED)
            for t in done:
                pnum = inflight.pop(t)
                results[pnum] = t.result()
                completed += 1
                logger.info(
                    f"[{filename}] Page {completed}/{page_count} processed | "
                    f"elapsed {time.time() - start_time:.1f}s"
                )
            # Yield to event loop — lets other requests' coroutines submit their next pages
            await asyncio.sleep(0)

        logger.info(f"[{filename}] All {page_count} pages done in {time.time() - start_time:.1f}s")

        pages_text = []
        for i, page_result in enumerate(results):
            if not page_result or not page_result.get('success'):
                raise Exception(
                    f"{filename} page {i+1} failed: "
                    f"{page_result.get('error', 'unknown') if page_result else 'no result'}"
                )
            pages_text.append(page_result['text'])

        clean_metadata = {k: v for k, v in metadata.items() if k != '_pdf_path'}
        return TextDoc(text=" ".join(pages_text), metadata=clean_metadata)

    finally:
        pdf_path_to_remove = metadata.get('_pdf_path')
        if pdf_path_to_remove and os.path.exists(pdf_path_to_remove):
            os.remove(pdf_path_to_remove)
            logger.info(f"Removed temporary PDF {pdf_path_to_remove}")

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.TEXT_EXTRACTOR,
    endpoint=str(MegaServiceEndpoint.TEXT_EXTRACTOR),
    host="0.0.0.0",
    port=int(os.getenv('TEXT_EXTRACTOR_USVC_PORT', default=9398)),
    input_datatype=DataPrepInput,
    output_datatype=TextSplitterInput,
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def process(input: DataPrepInput) -> TextSplitterInput:
    start = time.time()

    files = input.files
    link_list = input.links
    texts = input.texts

    logger.debug(f"Dataprep files: {files}")
    logger.debug(f"Dataprep link list: {link_list}")
    logger.debug(f"Dataprep texts: {texts}")

    # Decode files into (filename, bytes) — raw bytes are picklable for pool submission
    decoded_files: list[tuple[str, bytes]] = []
    if files:
        try:
            for fidx, f in enumerate(files):
                if not f.filename:
                    raise ValueError(f"File #{fidx} filename was empty.")
                if not is_valid_filename(f.filename):
                    raise ValueError(f"File {f.filename} has an invalid filename.")
                if not f.data64:
                    raise ValueError(f"File {f.filename} base64 data was empty.")
                file_data = base64.b64decode(f.data64)
                if not file_data:
                    raise ValueError(f"File {f.filename} base64 data was invalid.")
                decoded_files.append((f.filename, file_data))
        except ValueError as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="An error occurred while decoding files.")
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status_code=500, detail="An error occured while persisting files.")

    loop = asyncio.get_event_loop()
    upload_folder = os.getenv('UPLOAD_PATH', '/tmp/opea_upload')

    # Collect async tasks: one windowed coroutine per PDF, one future per non-PDF/link.
    all_tasks: list = []

    # Non-PDF files — one pool task each
    for filename, file_bytes in decoded_files:
        if not filename.lower().endswith('.pdf'):
            all_tasks.append(loop.run_in_executor(pool, run_single_file, filename, file_bytes, ASR_MODEL_SERVER_ENDPOINT))

    # Links — one pool task each
    for link in (link_list or []):
        all_tasks.append(loop.run_in_executor(pool, run_single_link, link, ASR_MODEL_SERVER_ENDPOINT))

    # PDFs — each file gets its own _process_pdf_windowed coroutine.
    # The windowed approach submits only _max_workers pages at a time and yields
    # to the event loop after each completion. This ensures concurrent requests
    # interleave their pages in the pool instead of one request monopolising all workers.
    for filename, file_bytes in decoded_files:
        if not filename.lower().endswith('.pdf'):
            continue
        Path(upload_folder).mkdir(parents=True, exist_ok=True)
        pdf_path = os.path.join(upload_folder, f"{uuid.uuid4()}_{filename}")
        with open(pdf_path, 'wb') as fout:
            fout.write(file_bytes)
        os.chmod(pdf_path, 0o600)

        doc = pymupdf.open(pdf_path)
        page_count = doc.page_count
        doc.close()
        logger.info(f"{filename}: {page_count} pages — starting windowed processing ({_max_workers} workers)")

        metadata = {'filename': filename, 'timestamp': time.time(), '_pdf_path': pdf_path}
        all_tasks.append(asyncio.ensure_future(_process_pdf_windowed(pdf_path, filename, page_count, metadata)))

    # Plain texts — no CPU work, handle inline
    loaded_docs: list[TextDoc] = []
    if texts:
        for text in texts:
            if text.strip() == "":
                logger.warning("Empty text found, skipping...")
                continue
            loaded_docs.append(TextDoc(text=text, metadata={'timestamp': time.time()}))

    if all_tasks:
        try:
            results = await asyncio.gather(*all_tasks)
        except HTTPError as e:
            logger.exception(e)
            raise HTTPException(status_code=400, detail=f"A HTTP Error occurred while processing links: {str(e)}")
        except (ConnectionError, ProxyError) as e:
            logger.exception(e)
            raise HTTPException(status_code=400, detail=f"Could not connect to remote server: {str(e)}")
        except ValueError as e:
            logger.exception(e)
            raise HTTPException(status_code=400, detail=f"A Value Error occurred while processing: {str(e)}")
        except MaxRetryError as e:
            logger.exception(e)
            raise HTTPException(status_code=503, detail=f"Could not connect to remote server: {str(e)}")
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status_code=500, detail=f"An error occurred while processing: {str(e)}")

        for result in results:
            if isinstance(result, TextDoc):
                loaded_docs.append(result)      # PDF windowed coroutine result
            elif isinstance(result, list):
                loaded_docs.extend(result)      # non-PDF file / link result list

    if not loaded_docs:
        raise HTTPException(status_code=400, detail="No documents were extracted from the provided input.")

    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    return TextSplitterInput(loaded_docs=loaded_docs)


if __name__ == "__main__":
    # Start the microservice
    validate_asr_endpoint(ASR_MODEL_SERVER_ENDPOINT)
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")
