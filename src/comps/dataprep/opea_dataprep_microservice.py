# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
import base64
import io
from dotenv import load_dotenv
from utils import opea_dataprep
from fastapi import UploadFile, HTTPException
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
dataprep = opea_dataprep.OPEADataprep(
    chunk_size=int(sanitize_env(os.getenv("CHUNK_SIZE"))),
    chunk_overlap=int(sanitize_env(os.getenv("CHUNK_OVERLAP"))),
    process_table=sanitize_env(os.getenv("PROCESS_TABLE")),
    table_strategy=sanitize_env(os.getenv("PROCESS_TABLE_STRATEGY"))
)

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
            for f in files:
                file_data = base64.b64decode(f.data64)
                binary_file = io.BytesIO(file_data)
                decoded_file = UploadFile(filename=f.filename, file=binary_file)
                decoded_files.append(decoded_file)
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status_code=500, detail="An error occured while persisting files.")

    textdocs = None
    try:
        textdocs = await dataprep.dataprep(files=decoded_files, link_list=link_list)
    except ValueError as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=f"An internal error occurred while processing: {str(e)}")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing: {str(e)}")

    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    return TextDocList(docs=textdocs)


if __name__ == "__main__":
    # Start the microservice
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")
