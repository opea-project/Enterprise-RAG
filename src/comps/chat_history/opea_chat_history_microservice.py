# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import os
import jwt

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request
from typing import Optional

from comps import change_opea_logger_level, get_opea_logger, MegaServiceEndpoint, ServiceType
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.proto.docarray import ChatHistory, ChatHistoryName
from comps.cores.utils.utils import sanitize_env

from utils.opea_chat_history import OPEAChatHistoryConnector

# Define the unique service name for the microservice
USVC_NAME='opea_service@chat_history'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

opea_connector = OPEAChatHistoryConnector(sanitize_env(os.getenv("CHAT_HISTORY_MONGO_HOST")),
                                          sanitize_env(os.getenv("CHAT_HISTORY_MONGO_PORT")),
                                          )


def get_user_id(request: Request) -> str:
    access_token = request.headers.get('Authorization')
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization header missing Provide the correct header.")
    access_token = access_token.replace('Bearer ', '')

    token = jwt.decode(access_token, options={"verify_signature": False})
    user_id = token.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token. Provide the correct token.")
    return user_id


@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.CHAT_HISTORY,
    endpoint=f"{MegaServiceEndpoint.CHAT_HISTORY}/save",
    http_method="POST",
    host="0.0.0.0",
    port=int(os.getenv('CHAT_HISTORY_USVC_PORT', default=6012)),
    startup_methods=[opea_connector.init_async],
    close_methods=[opea_connector.close]
)
async def save_history(document: ChatHistory, user_id: str = Depends(get_user_id)):
    """Saves or updates chat history.

    Args:
        document (ChatHistory): The ChatHistory object containing the history to be stored.

    Returns:
        ChatHistoryName, raises HTTPException otherwise.
    """
    try:
        if document.id:
            res = await opea_connector.append_history(document.id, document.history, user_id)
        else:
            res = await opea_connector.create_new_history(document.history, user_id)
        return res
    except ValueError as e:
        error_message = f"A ValueError occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    except Exception as e:
        error_message = f"An error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message)


@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.CHAT_HISTORY,
    endpoint=f"{MegaServiceEndpoint.CHAT_HISTORY}/get",
    http_method="GET",
    host="0.0.0.0",
    port=int(os.getenv('CHAT_HISTORY_USVC_PORT', default=6012)),
    startup_methods=[opea_connector.init_async],
    close_methods=[opea_connector.close]
)
async def get_history(history_id: Optional[str] = None, user_id: str = Depends(get_user_id)):
    """Retrieves documents from the document store based on the provided ChatId.

    Args:
        document (ChatId): The ChatId object containing the user and optional document id.

    Returns:
        The retrieved documents if successful, raises HTTPException otherwise.
    """
    try:
        if history_id is None:
            res = await opea_connector.get_all_histories_for_user(user_id)
        else:
            res = await opea_connector.get_history_by_id(history_id, user_id)
        return res
    except ValueError as e:
        error_message = f"A ValueError occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    except Exception as e:
        error_message = f"An error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message)


@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.CHAT_HISTORY,
    endpoint=f"{MegaServiceEndpoint.CHAT_HISTORY}/delete",
    http_method="DELETE",
    host="0.0.0.0",
    port=int(os.getenv('CHAT_HISTORY_USVC_PORT', default=6012)),
    startup_methods=[opea_connector.init_async],
    close_methods=[opea_connector.close]
)
async def delete_history(history_id: str, user_id: str = Depends(get_user_id)):
    """Deletes a document from the document store based on the provided ChatId.

    Args:
        document (ChatId): The ChatId object containing the user and document id.

    Returns:
        None if successful, raises HTTPException otherwise.
    """
    try:
        await opea_connector.delete_history(history_id, user_id)
    except ValueError as e:
        error_message = f"A ValueError occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    except Exception as e:
        error_message = f"An error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message)


@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.CHAT_HISTORY,
    endpoint=f"{MegaServiceEndpoint.CHAT_HISTORY}/change_name",
    http_method="POST",
    host="0.0.0.0",
    port=int(os.getenv('CHAT_HISTORY_USVC_PORT', default=6012)),
    startup_methods=[opea_connector.init_async],
    close_methods=[opea_connector.close]
)
async def change_history_name(history_name: ChatHistoryName, user_id: str = Depends(get_user_id)):
    """Deletes a document from the document store based on the provided ChatId.

    Args:
        document (ChatId): The ChatId object containing the user and document id.

    Returns:
        None if successful, raises HTTPException otherwise.
    """
    try:
        await opea_connector.change_history_name(history_name.id, history_name.history_name, user_id)
    except ValueError as e:
        error_message = f"A ValueError occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    except Exception as e:
        error_message = f"An error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message)


if __name__ == "__main__":
    # Start the microservice
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")
