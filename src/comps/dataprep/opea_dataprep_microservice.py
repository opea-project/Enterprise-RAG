# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
from concurrent.futures import ProcessPoolExecutor
import os
import time
import base64
import io

from urllib3.exceptions import MaxRetryError
from dotenv import load_dotenv
from utils import opea_dataprep
from fastapi import UploadFile, HTTPException
from pathvalidate import is_valid_filename
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from comps.cores.utils.utils import sanitize_env
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceType
from comps.cores.proto.docarray import DataPrepInput, TextDocList
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.mega.base_statistics import register_statistics, statistics_dict

# Define the unique service name for the microservice
USVC_NAME='opea_service@opea_dataprep'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEADataprep class with environment variables.
def run_dataprep(files, links):
    dataprep = opea_dataprep.OPEADataprep(
        chunk_size=int(sanitize_env(os.getenv("CHUNK_SIZE"))),
        chunk_overlap=int(sanitize_env(os.getenv("CHUNK_OVERLAP"))),
        process_table=sanitize_env(os.getenv("PROCESS_TABLE")),
        table_strategy=sanitize_env(os.getenv("PROCESS_TABLE_STRATEGY"))
    )
    textdocs = dataprep.dataprep(files=files, link_list=links)
    return textdocs

# Process Pool Executor was introduced due to API being unresponsive while computing non-io tasks.
# Originally, async functions are run in event loop which means that they block the server thread
# thus making it unresponsive for other requests - mainly health_check - which then might cause
# some issues on k8s deployments, showing the pod as not ready by failing the liveness probe.
# While moving it to sync function fixed that issue this meant that it would run in a separate
# thread but was instead slower due to not using async io calls. The resolution is to run it
# as an async function for io improvement, but spawn a separate process for heavy CPU usage calls.
# Setting max_workers to 1 ensures that the CPU heavy calls are not overutilizing the pod resources.
# https://github.com/fastapi/fastapi/issues/3725#issuecomment-902629033
# https://luis-sena.medium.com/how-to-optimize-fastapi-for-ml-model-serving-6f75fb9e040d
pool = ProcessPoolExecutor(max_workers=1)

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.DATAPREP,
    endpoint=str(MegaServiceEndpoint.DATAPREP),
    host="0.0.0.0",
    port=int(os.getenv('DATAPREP_USVC_PORT', default=9399)),
    input_datatype=DataPrepInput,
    output_datatype=TextDocList,
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def process(input: DataPrepInput) -> TextDocList:
    start = time.time()

    files = input.files
    link_list = input.links

    logger.debug(f"Dataprep files: {files}")
    logger.debug(f"Dataprep link list: {link_list}")

    decoded_files = []
    if files:
        try:
            for fidx, f in enumerate(files):
                if not f.filename:
                    raise ValueError(f"File #{fidx} filename was empty.")
                if not is_valid_filename(f.filename):
                    raise ValueError(f"File {f.filename} had an invalid filename.")
                if not f.data64:
                    raise ValueError(f"File {f.filename} base64 data was empty.")
                file_data = base64.b64decode(f.data64)
                if not file_data:
                    raise ValueError(f"File {f.filename} base64 data was invalid.")
                binary_file = io.BytesIO(file_data)
                decoded_file = UploadFile(filename=f.filename, file=binary_file)
                decoded_files.append(decoded_file)
        except ValueError as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="An error occurred while decoding files.")
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status_code=500, detail="An error occured while persisting files.")

    textdocs = None
    loop = asyncio.get_event_loop()
    try:
        textdocs = await loop.run_in_executor(pool, run_dataprep, decoded_files, link_list)
    except ValueError as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=f"An internal error occurred while processing: {str(e)}")
    except MaxRetryError as e:
        logger.exception(e)
        raise HTTPException(status_code=503, detail=f"Could not connect to remote server: {str(e)}")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing: {str(e)}")

    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    return TextDocList(docs=textdocs)


if __name__ == "__main__":
    # Start the microservice
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")
