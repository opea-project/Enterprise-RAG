# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from dotenv import dotenv_values
from fastapi import HTTPException

from comps.cores.mega.micro_service import (
    opea_microservices,
    register_microservice
)
from comps import (
    MegaServiceEndpoint,
    PromptCreate,
    PromptGet,
    PromptId,
    PromptOutput,
    change_opea_logger_level,
    get_opea_logger
)

from utils.opea_prompt_registry import OPEAPromptRegistryConnector

USVC_NAME = "opea_service@prompt_registry"

config = {
    **dotenv_values("./impl/microservice/.env"),
    **os.environ,
}

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, os.getenv("OPEA_LOGGER_LEVEL", "INFO"))


opea_connector = OPEAPromptRegistryConnector(config["PROMPT_REGISTRY_MONGO_HOST"],
                                             config["PROMPT_REGISTRY_MONGO_PORT"],
                                             )


@register_microservice(
    name=USVC_NAME,
    endpoint=f"{MegaServiceEndpoint.PROMPT_REGISTRY}/create",
    host="0.0.0.0",
    port=int(os.getenv('PROMPT_REGISTRY_USVC_PORT', default=6012)),
    input_datatype=PromptCreate,
    output_datatype=PromptId,
    startup_methods=[opea_connector.init_async],
    close_methods=[opea_connector.close]
)
async def create_prompt(prompt: PromptCreate) -> PromptId:
    logger.info(f"Received input: {prompt}")

    if prompt.prompt_text == "":
        raise HTTPException(status_code=400, detail="Prompt text is empty. Provide a valid prompt.")

    if prompt.filename == "":
        raise HTTPException(status_code=400, detail="Filename is empty. Provide a valid filename.")

    try:
        id = await opea_connector.insert_prompt(prompt.prompt_text, prompt.filename)
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    output = PromptId(prompt_id=id)
    return output


@register_microservice(
    name=USVC_NAME,
    endpoint=f"{MegaServiceEndpoint.PROMPT_REGISTRY}/get",
    host="0.0.0.0",
    port=int(os.getenv('PROMPT_REGISTRY_USVC_PORT', default=6012)),
    input_datatype=PromptGet,
    output_datatype=PromptOutput,
    startup_methods=[opea_connector.init_async],
    close_methods=[opea_connector.close]
)
async def get_prompt(prompt: PromptGet) -> PromptOutput:
    def is_string_empty(s: str) -> bool:
        return s is None or s.strip() == ""

    id = prompt.prompt_id
    filename = prompt.filename
    text = prompt.prompt_text

    try:
        if is_string_empty(id) and is_string_empty(filename) and is_string_empty(text):
            logger.info(f"Received input: {prompt}. Getting all prompts.")
            output = await opea_connector.get_all_prompts()
        elif is_string_empty(id) and not is_string_empty(filename) and is_string_empty(text):
            logger.info(f"Received input: {prompt}. Getting prompts for filename: {filename}")
            output = await opea_connector.get_prompts_by_filename(filename)
        elif is_string_empty(id) and is_string_empty(filename) and not is_string_empty(text):
            logger.info(f"Received input: {prompt}. Getting prompts based on keyword {text}.")
            output = await opea_connector.get_prompts_by_text(text)
        elif is_string_empty(id) and not is_string_empty(text) and not is_string_empty(filename):
            logger.info(f"Received input: {prompt}. Getting prompts based on keyword {text} and filename: {filename}.")
            output = await opea_connector.get_prompts_by_filename_and_text(filename, text)
        elif not is_string_empty(id):
            logger.info(f"Received input: {prompt}. Getting prompt with ID: {id}")
            output = await opea_connector.get_prompt_by_id(id)
            if output is not None:
                output = [output]
        else:
            raise HTTPException(status_code=400, detail="Invalid input. Provide a valid prompt ID, filename, or prompt text.")
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    if output is None:
        output = []

    outputs = []
    for o in output:
        outputs.append(PromptGet(prompt_id=str(o.id), prompt_text=o.prompt_text, filename=o.filename))
    res = PromptOutput(prompts=outputs)
    return res


@register_microservice(
    name=USVC_NAME,
    endpoint=f"{MegaServiceEndpoint.PROMPT_REGISTRY}/delete",
    host="0.0.0.0",
    port=int(os.getenv('PROMPT_REGISTRY_USVC_PORT', default=6012)),
    input_datatype=PromptId,
    startup_methods=[opea_connector.init_async],
    close_methods=[opea_connector.close]
)
async def delete_prompt(prompt: PromptId):
    logger.info(prompt)

    if prompt.prompt_id is not None and prompt.prompt_id == "":
        raise HTTPException(status_code=400, detail="Prompt ID is empty. Provide a valid prompt ID.")

    try:
        await opea_connector.delete_prompt(prompt.prompt_id)
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Prompt Suggestion microservice: {USVC_NAME}")
