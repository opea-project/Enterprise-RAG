# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
import os
from comps.guardrails.llm_guard_scanners.output_scanner.utils import llm_guard_output_scanner
from fastapi import Request
from fastapi.responses import StreamingResponse

from comps import get_opea_logger

logger = get_opea_logger("llm_guard_output_scanner_microservice") # TODO: to be changed to after folder structure changes

from comps import (
    GeneratedDoc,
    ServiceType,
    MegaServiceEndpoint,
    get_opea_logger,
    change_opea_logger_level,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

def start_llm_guard_output_scanner_service(llm_guard_output_scanner: llm_guard_output_scanner.LLMGuardOutputScanner, opea_microservice_name: str):
    """Create the embedding service with the given LLM Guard output scanner.

    Args:
        llm_guard_output_scanner (llm_guard_output_scanner.LLMGuardOutputScanner): An instance of LLM Guard Onput Scanner class.
        opea_microservice_name (str): The name of the microservice.
    """

    @register_microservice(
        name=opea_microservice_name,
        service_type=ServiceType.LLM_GUARD_OUTPUT_SCANNER,
        endpoint=str(MegaServiceEndpoint.LLM_GUARD_OUTPUT_SCANNER),
        host="0.0.0.0",
        port=8060,
        input_datatype=Request,
        output_datatype=GeneratedDoc
    )
    @register_statistics(names=[opea_microservice_name])
    async def output_scanner(llm_output: Request) -> GeneratedDoc:
        start = time.time()
        content_type = llm_output.headers.get('content-type')
        if content_type == 'application/json':
            data = await llm_output.json()
            try:
                doc = GeneratedDoc(**data)
            except Exception as e:
                logger.error(f"Problem with creating GenerateDoc: {e}")
            sanitized_output = llm_guard_output_scanner.scan_llm_output(doc.prompt, doc.text)
            statistics_dict[opea_microservice_name].append_latency(time.time() - start, None)
            return GeneratedDoc(text=sanitized_output, prompt=doc.prompt)
        else:
            data = await llm_output.body() # TODO: to be changed, because output.body() get whole text probably
            try:
                doc = data.decode("utf-8")
            except Exception as e:
                logger.error(f"Problem with decoding the streaming {e}")

            def stream_generator(chunk):
                yield chunk

            sanitized_output = llm_guard_output_scanner.scan_llm_output('', doc) # TODO: probably dedicated function
            return StreamingResponse(stream_generator(doc), media_type="text/event-stream")

            #statistics_dict[opea_microservice_name].append_latency(time.time() - start, None)

    opea_microservices[opea_microservice_name].start()

if __name__ == "__main__":
    try:
        log_level = os.getenv("OPEA_LOGGER_LEVEL", "INFO")
        change_opea_logger_level(logger, log_level)
        config = ['BanSubstrings', 'JSON', 'ReadingTime', 'Regex', 'URLReachability'] #TODO: make config configurable through k8s
        output_scanner = llm_guard_output_scanner.LLMGuardOutputScanner(config)
        opea_microservice_name = "opea_service@llm_guard_output_scanner"
        start_llm_guard_output_scanner_service(output_scanner, opea_microservice_name)
    except Exception as e:
        logger.exception(f"Error initializing LLMGuardOutputScanner: {e}")