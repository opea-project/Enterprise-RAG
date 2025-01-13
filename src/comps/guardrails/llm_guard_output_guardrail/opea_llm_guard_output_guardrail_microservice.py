# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from dotenv import dotenv_values
from fastapi import Request, HTTPException
from fastapi.responses import Response, StreamingResponse

from comps import (
    GeneratedDoc,
    ServiceType,
    MegaServiceEndpoint,
    get_opea_logger,
    change_opea_logger_level,
    opea_microservices,
    register_microservice,
    register_statistics,
)
from comps.guardrails.llm_guard_output_guardrail.utils.llm_guard_output_guardrail import (
    OPEALLMGuardOutputGuardrail
)

USVC_NAME = "opea_service@llm_guard_output_scanner"
logger = get_opea_logger("llm_guard_output_scanner_microservice") # TODO: to be changed to after folder structure changes

usvc_config = {
    **dotenv_values(".env"),
    **os.environ # override loaded values with environment variables - priotity
}

output_guardrail = OPEALLMGuardOutputGuardrail(usvc_config)

@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.LLM_GUARD_OUTPUT_SCANNER,
    endpoint=str(MegaServiceEndpoint.LLM_GUARD_OUTPUT_SCANNER),
    host="0.0.0.0",
    port=usvc_config.get('LLM_GUARD_INPUT_SCANNER_USVC_PORT', 8060),
    input_datatype=Request,
    output_datatype=Response
)

@register_statistics(names=[USVC_NAME])
async def process(llm_output: Request) -> Response: # GeneratedDoc or StreamingResponse
    """
    Process the LLM output using the OPEALLMGuardOutputGuardrail.

    This function processes the LLM output by sanitizing it using the LLM Guard Output Scanner.
    It handles both JSON and streaming responses.

    Args:
        llm_output (Request): The LLM output request to be processed.

    Returns:
        GeneratedDoc: The processed document with sanitized LLM output.
        StreamingResponse: The processed streaming response with sanitized LLM output.

    Raises:
        Exception: If there is an error creating the GeneratedDoc or decoding the streaming 
        response.
    """
    try:
        data = await llm_output.json()
        doc = GeneratedDoc(**data)
        if doc.output_guardrail_params is not None:
            output_guard_streaming = doc.output_guardrail_params.output_guard_streaming
        else:
            output_guard_streaming = True
    except Exception as e:
        logger.error(f"Problem with creating GenerateDoc: {e}")
        raise HTTPException(status_code=500, detail=f"{e}") from e

    scanned_output = output_guardrail.scan_llm_output(doc)

    if output_guard_streaming is False:
        return GeneratedDoc(text=scanned_output, prompt=doc.prompt)
    else:
        generator = scanned_output.split()
        def stream_generator():
            chat_response = ""
            try:
                for text in generator:
                    chat_response += text
                    chunk_repr = repr(' ' + text) # Guard is streaming, when LLM is not. Space needed for UI to show properly the output
                    logger.debug("[guard - chat_stream] chunk:{chunk_repr}")
                    yield f"data: {chunk_repr}\n\n"
                logger.debug("[guard - chat_stream] stream response: {chat_response}")
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Error streaming from Guard: {e}")
                yield "data: [ERROR]\n\n"
        return StreamingResponse(stream_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    log_level = usvc_config.get("OPEA_LOGGER_LEVEL", "INFO")
    change_opea_logger_level(logger, log_level)
    
    opea_microservices[USVC_NAME].start()
