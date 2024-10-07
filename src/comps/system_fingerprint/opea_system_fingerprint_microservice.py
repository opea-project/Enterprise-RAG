# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import List
from comps.system_fingerprint.utils.opea_system_fingerprint import OPEASystemFingerprintController
from comps.cores.proto.docarray import ComponentArgument
from comps import get_opea_logger, change_opea_logger_level, MegaServiceEndpoint
from fastapi import HTTPException
from comps import (
    sanitize_env
)

import os
from comps.cores.mega.micro_service import (
    opea_microservices,
    register_microservice
)
from typing import Dict

USVC_NAME = "opea_service@system_fingerprint"

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

mongo_controller = OPEASystemFingerprintController(
    db_name=sanitize_env(os.getenv("MONGODB_NAME")),
    mongodb_host=sanitize_env(os.getenv("SYSTEM_FINGERPRINT_MONGODB_HOST")),
    mongodb_port=int(os.getenv("SYSTEM_FINGERPRINT_MONGODB_PORT")))


@register_microservice(
    name=USVC_NAME,
    endpoint=f"{MegaServiceEndpoint.SYSTEM_FINGERPRINT}/append_arguments",
    host="0.0.0.0",
    port=int(os.getenv('SYSTEM_FINGERPRINT_USVC_PORT', default=6012)),
    input_datatype=Dict,
    output_datatype=None,
    startup_methods=[mongo_controller.init_async],
    close_methods=[mongo_controller.close]
)
async def append_arguments(input: Dict) -> Dict:
    if not input:
        raise HTTPException(status_code=400, detail="Input is empty.")
    try:
        packed_arguments = await mongo_controller.pack_arguments()
        input.update(packed_arguments)
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}")

    return input


@register_microservice(
    name=USVC_NAME,
    endpoint=f"{MegaServiceEndpoint.SYSTEM_FINGERPRINT}/change_arguments",
    host="0.0.0.0",
    port=int(os.getenv('SYSTEM_FINGERPRINT_USVC_PORT', default=6012)),
    input_datatype=List[ComponentArgument],
    output_datatype=None,
    startup_methods=[mongo_controller.init_async],
    close_methods=[mongo_controller.close]
)
async def change_arguments(inputs: List[ComponentArgument]) -> None:
    if not inputs:
        raise HTTPException(status_code=400, detail="Input is empty.")
    try:
        await mongo_controller.store_arguments(inputs)
    except HTTPException as e:
        logger.exception(f"An error occurred: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA System Fingerprint microservice: {USVC_NAME}")
