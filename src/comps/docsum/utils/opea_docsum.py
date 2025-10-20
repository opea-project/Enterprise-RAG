# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import requests
import time

from fastapi.responses import StreamingResponse
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from typing import Union

from comps.cores.proto.docarray import TextDocList, GeneratedDoc
from comps.cores.mega.logger import get_opea_logger
from comps.docsum.utils.templates import templ_en, templ_refine_en


logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

SUPPORTED_SUMMARY_TYPES = ["map_reduce", "refine", "stuff"]

class OPEADocsum:
    """OPEA Document Summarization Component."""
    def __init__(self, llm_usvc_endpoint: str, default_summary_type: str = "map_reduce"):
        """
        Initialize the OPEADocsum component.

        Args:
            default_summary_type (str): The default summary type to use if not specified in the request.
            llm_usvc_endpoint (str): The endpoint of the LLM microservice to use for summarization.
        """
        default_summary_type = default_summary_type.lower()
        if default_summary_type not in SUPPORTED_SUMMARY_TYPES:
            raise ValueError(f"Unsupported default_summary_type: {default_summary_type}. Supported types are: {SUPPORTED_SUMMARY_TYPES}")
        if not llm_usvc_endpoint:
            raise ValueError("LLM microservice endpoint must be provided and non-empty.")

        self.default_summary_type = default_summary_type
        self.llm_usvc_endpoint = llm_usvc_endpoint

        self._validate()

    def _validate(self) -> None:
        """Validate the configuration by making a test call to the LLM microservice."""
        tested_params = {
                "messages": [{"role": "system", "content": "test"}, {"role": "user", "content": "test"}],
                "max_new_tokens": 5
                }
        try:
            response = requests.post(f"{self.llm_usvc_endpoint}/chat/completions", json=tested_params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to connect to LLM microservice at {self.llm_usvc_endpoint}: {e}")
            raise ConnectionError(f"Failed to connect to LLM microservice at {self.llm_usvc_endpoint}: {e}")

        logger.info("OPEADocsum configuration validated successfully.")


    async def run(self, input: TextDocList) -> Union[GeneratedDoc, StreamingResponse]:
        """
        Process the given TextDocList input and return a summary.

        Args:
            input (TextDocList): The input documents to summarize.
        """
        start_time = time.time()
        if not input.summary_type:
            summary_type = self.default_summary_type
        else:
            summary_type = input.summary_type.lower()
            if summary_type not in SUPPORTED_SUMMARY_TYPES:
                raise ValueError(f"Unsupported summary_type: {summary_type}. Supported types are: {SUPPORTED_SUMMARY_TYPES}")
        use_stream = input.stream if input.stream is not None else True

        client = ChatOpenAI(base_url=self.llm_usvc_endpoint,
                            api_key="dummy"
                            )

        logger.debug(f"Input documents count: {len(input.docs)}")
        logger.debug(f"Using summary_type: {summary_type}")
        logger.debug(f"Streaming response: {use_stream}")

        prompt = PromptTemplate.from_template(templ_en)
        if summary_type == "map_reduce":
            chain = load_summarize_chain(llm=client,
                                         chain_type=summary_type,
                                         map_prompt=prompt,
                                         combine_prompt=prompt,
                                         return_intermediate_steps=True
                                         )
        elif summary_type == "refine":
            prompt_refine = PromptTemplate.from_template(templ_refine_en)
            chain = load_summarize_chain(llm=client,
                                         question_prompt=prompt,
                                         refine_prompt=prompt_refine,
                                         chain_type="refine",
                                         return_intermediate_steps=True
                                         )
        elif summary_type == "stuff":
            chain = load_summarize_chain(llm=client,
                                         prompt=prompt,
                                         chain_type=summary_type
                                         )
        else:
            raise ValueError(f"Unsupported summary_type: {summary_type}. Supported types are: {SUPPORTED_SUMMARY_TYPES}")

        docs = [Document(page_content=t.text) for t in input.docs]

        if use_stream:
            async def stream_generator():
                try:
                    # Use astream_events for better control over streaming
                    # This provides token-by-token streaming from the underlying LLM
                    async for event in chain.astream_events(docs, version="v2"):
                        kind = event["event"]

                        # Stream only the actual LLM token outputs
                        if kind == "on_chat_model_stream":
                            content = event["data"]["chunk"].content
                            if content:
                                # logger.debug(f"Streaming token: {content}")
                                yield f"data: {content}\n\n"

                        # Optionally include intermediate summaries for map_reduce/refine
                        elif kind == "on_chain_end" and "output_text" in event["data"].get("output", {}):
                            output_text = event["data"]["output"]["output_text"]
                            logger.debug(f"Final summary: {output_text}")

                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield f"data: [ERROR] {str(e)}\n\n"

                yield "data: [DONE]\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            response = await chain.ainvoke(docs)
            # Only map_reduce and refine return intermediate_steps
            if "intermediate_steps" in response and logger.isEnabledFor(logging.DEBUG):
                intermediate_steps = response["intermediate_steps"]
                logger.debug("intermediate_steps:")
                for step in intermediate_steps:
                    logger.debug(step)

            output_text = response["output_text"]
            logger.info(f"SUMMARY: {output_text}")
            logger.info(f"Summarization completed in {time.time() - start_time:.3f} seconds.")
            return GeneratedDoc(text=output_text, prompt="", stream=False)
