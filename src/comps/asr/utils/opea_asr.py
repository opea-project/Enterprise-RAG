# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# TODO: Implement a Generic Connector

from fastapi import Request, HTTPException
from fastapi.responses import Response, StreamingResponse
import uuid
from comps import get_opea_logger
import json
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEAASR:

    _instance = None

    def __new__(cls, model_name: str, model_server: str, endpoint: str):

        if cls._instance is None:
            cls._instance = super(OPEAASR, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server):
                logger.warning(f"Existing OPEAASR instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, model_server: str, endpoint: str) -> None:
        """
        Initializes the OPEAASR instance.

        Args:
            model_name (str): The full name of the model, which may include the repository ID (e.g., 'openai/whisper-small'). 
                      Internally, only the short name (the last part after the final '/') will be used. For instance, 
                      'whisper-small' will be extracted from 'whisper-small'.

            model_server (str): The URL of the model server.
            endpoint (str): The endpoint for the model server.
        """
        self._model_name = model_name.split('/')[-1].lower()    # Extract the last part of the model name
        self._model_server = model_server.lower()
        self._endpoint = endpoint
        self._APIs = []

    async def asr(self, input_data):
        logger.info("reached asr")
        self._endpoint = self._endpoint.rstrip('/')
        url = self._endpoint + f"/predictions/{self._model_name.split('/')[-1]}"
        logger.info(url)
        try:
            from huggingface_hub import (
                    AsyncInferenceClient,
                )
            self.async_client = AsyncInferenceClient(
                    model=f"{url}",
                )
        except ImportError as e:
            error_message =  "Could not import huggingface_hub python package.\n" \
                                "Please install it with `pip install huggingface_hub`.\n"  \
                                f"Error: {e}"
            logger.exception(error_message)
            raise
        try:
            responses = await self.async_client.post(
                data=input_data
            )
            logger.info(f"Received response: {responses}")

            return Response(responses)
        except Exception as e:
            logger.exception(f"Error embedding documents: {e}")
            raise

    async def run(self, request_data) -> Response:
        """
        Processes the input audio using the OPEAASR.

        Args:
            input: The input audio to be processed.

        Returns:
            Response
        """
        #logger.info(f"Received request data: {request_data}")
        #print(request_data)

        #if request_data['model'] not in ["openai/whisper-small"]:
        #    raise Exception("ASR model mismatch! Currently only support model: openai/whisper-small")

        try:
            response = await self.asr(request_data)
            return response
        except Exception as e:
            logger.exception(f"Error processing ASR request: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        

