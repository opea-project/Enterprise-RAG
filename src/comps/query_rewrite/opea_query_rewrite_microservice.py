# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Query Rewriting Microservice."""

import os
import time

from dotenv import load_dotenv
from fastapi import HTTPException, Request

from comps import (
    TextDoc,
    MegaServiceEndpoint,
    ServiceType,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
    sanitize_env,
    statistics_dict,
)
from comps.query_rewrite.utils.opea_query_rewrite import OPEAQueryRewrite

USVC_NAME = "opea_service@query_rewrite"

load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

opea_query_rewrite = OPEAQueryRewrite(
    llm_endpoint=sanitize_env(os.getenv("QUERY_REWRITE_LLM_ENDPOINT")),
    chat_history_endpoint=sanitize_env(os.getenv("CHAT_HISTORY_ENDPOINT")),
    timeout=int(os.getenv("QUERY_REWRITE_TIMEOUT", 30)),
    max_concurrency=int(os.getenv("QUERY_REWRITE_MAX_CONCURRENCY", 8)),
)


def _get_access_token(request: Request) -> str:
    access_token = request.headers.get("Authorization", "")
    if access_token.startswith("Bearer "):
        return access_token[7:]
    return ""


@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.QUERY_REWRITE,
    endpoint=str(MegaServiceEndpoint.QUERY_REWRITE),
    host="0.0.0.0",
    port=int(os.getenv("QUERY_REWRITE_USVC_PORT", 6626)),
    input_datatype=TextDoc,
    output_datatype=TextDoc,
    validate_methods=[opea_query_rewrite._validate],
)
@register_statistics(names=[USVC_NAME])
async def process(input: TextDoc, request: Request) -> TextDoc:
    start_time = time.time()

    logger.info(
        f"[REQUEST] Received query: '{input.text[:100]}{'...' if len(input.text) > 100 else ''}', "
        f"history_id: {input.history_id or 'None'}"
    )
    logger.debug(
        f"[REQUEST] metadata keys: {list(input.metadata.keys()) if input.metadata else []}"
    )

    parameters = input.metadata.get("parameters", {}) if input.metadata else {}
    query_rewrite_params = parameters.get("query_rewrite_params", {})
    max_new_tokens = query_rewrite_params.get("max_new_tokens")
    temperature = query_rewrite_params.get("temperature")

    logger.debug(
        f"[REQUEST] query_rewrite_params from fingerprint: max_new_tokens={max_new_tokens}, temperature={temperature}"
    )

    try:
        access_token = _get_access_token(request)
        logger.debug(f"[REQUEST] Has Authorization header: {bool(access_token)}")

        result = await opea_query_rewrite.run(
            input,
            access_token,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        result.history_id = input.history_id

        elapsed = time.time() - start_time
        logger.info(
            f"[RESPONSE] Query rewritten in {elapsed:.2f}s: "
            f"'{result.text[:100]}{'...' if len(result.text) > 100 else ''}'"
        )

        statistics_dict[USVC_NAME].append_latency(elapsed, None)
        return result

    except ValueError as e:
        logger.exception(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except ConnectionError as e:
        logger.exception(f"Connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    logger.info(f"Starting {USVC_NAME}")
    opea_microservices[USVC_NAME].start()
