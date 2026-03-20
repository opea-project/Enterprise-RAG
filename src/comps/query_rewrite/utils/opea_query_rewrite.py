# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Query Rewriting using LLM for contextual rewriting and query refinement."""

import asyncio
import os
import re
import time
from typing import List, Optional

import httpx
import openai
import requests

from comps import TextDoc, get_opea_logger, change_opea_logger_level
from comps.cores.proto.docarray import PrevQuestionDetails
from comps.query_rewrite.utils.templates import (
    QUERY_REWRITE_SYSTEM_PROMPT,
    QUERY_REWRITE_WITH_HISTORY_SYSTEM_PROMPT,
    QUERY_REWRITE_USER_PROMPT,
    QUERY_REWRITE_WITH_HISTORY_USER_PROMPT,
)

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))


class OPEAQueryRewrite:
    """Query Rewriting component using LLM."""

    DEFAULT_MAX_NEW_TOKENS = 256
    DEFAULT_TEMPERATURE = 0.1

    def __init__(
        self,
        llm_endpoint: str,
        chat_history_endpoint: Optional[str] = None,
        timeout: int = 30,
        max_concurrency: int = 8,
    ):
        self.llm_endpoint = llm_endpoint
        self.chat_history_endpoint = chat_history_endpoint
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrency)

        if self.llm_endpoint and not self.llm_endpoint.rstrip("/").endswith("/v1"):
            self.llm_endpoint = self.llm_endpoint.rstrip("/") + "/v1"

        self._http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=max_concurrency),
            timeout=self.timeout,
        )

        self._client = openai.AsyncOpenAI(
            api_key="EMPTY",
            base_url=self.llm_endpoint,
            timeout=self.timeout,
            http_client=self._http_client,
        )

        self._model_name = self._fetch_model_name()
        self._validate()

        logger.info(
            f"Initialized with LLM endpoint: {self.llm_endpoint}, model: {self._model_name}"
        )

    def _fetch_model_name(self) -> str:
        """Fetch model name from vLLM endpoint at initialization (sync is OK at startup)."""
        try:
            response = requests.get(f"{self.llm_endpoint}/models", timeout=10)
            if response.status_code == 200:
                models = response.json().get("data", [])
                if models:
                    return models[0]["id"]
        except Exception as e:
            logger.error(f"Failed to get model name at init: {e}")
            raise
        return "default"

    async def _get_chat_history(
        self, history_id: str, access_token: str = ""
    ) -> List[PrevQuestionDetails]:
        """Retrieve chat history from Chat History service (async)."""
        logger.debug(f"[HISTORY] Fetching history for ID: {history_id}")

        if not self.chat_history_endpoint:
            logger.warning("[HISTORY] No chat_history_endpoint configured, skipping")
            return []

        if not access_token:
            logger.warning("[HISTORY] No access_token provided, skipping history fetch")
            return []

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        url = f"{self.chat_history_endpoint}/v1/chat_history/get?history_id={history_id}"
        logger.debug(f"[HISTORY] Calling: {url}")
        response = await self._http_client.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            raise ConnectionError(
                f"Chat history service returned HTTP {response.status_code} for history_id={history_id}"
            )

        data = response.json()
        history_items = data.get("history", [])
        logger.info(f"[HISTORY] Retrieved {len(history_items)} history items")
        return [
            PrevQuestionDetails(question=h["question"], answer=h["answer"])
            for h in history_items
        ]

    def _format_history(
        self,
        history: List[PrevQuestionDetails],
        max_turns: int = 3,
        max_answer_len: int = 500,
    ) -> str:
        """Format chat history for prompt.

        Args:
            history: List of previous Q&A pairs
            max_turns: Maximum number of conversation turns to include
            max_answer_len: Maximum length of each answer (truncated if longer)
        """
        if not history:
            return "No previous conversation."

        formatted = []
        for h in history[-max_turns:]:
            formatted.append(f"User: {h.question}")
            answer = (
                h.answer[:max_answer_len] + "..."
                if len(h.answer) > max_answer_len
                else h.answer
            )
            formatted.append(f"Assistant: {answer}")
        return "\n".join(formatted)

    async def _call_llm(
        self, system_prompt: str, user_prompt: str, max_new_tokens: int, temperature: float
    ) -> str:
        """Call LLM with given prompts."""
        logger.debug(f"[LLM] Calling model: {self._model_name}")
        logger.debug(f"[LLM] User prompt: {user_prompt[:100]}...")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        start_time = time.time()
        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            max_tokens=max_new_tokens,
            temperature=temperature,
        )
        elapsed = time.time() - start_time

        if not response.choices:
            logger.warning("[LLM] Empty response from LLM")
            return user_prompt.split(":")[
                -1
            ].strip()  # extract original query from prompt

        result = response.choices[0].message.content
        if not result:
            logger.warning("[LLM] None content in response")
            return user_prompt.split(":")[-1].strip()

        logger.info(
            f"[LLM] Response in {elapsed:.2f}s: '{result[:100]}...' (tokens: {response.usage.total_tokens if response.usage else 'N/A'})"
        )
        return result

    def _validate(self):
        tested_params = {
                "messages": [{"role": "system", "content": "test"}, {"role": "user", "content": "test"}],
                "max_new_tokens": 5
                }
        try:
            response = requests.post(f"{self.llm_endpoint}/chat/completions", json=tested_params, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to connect to VLLM at {self.llm_endpoint}: {e}")
            raise ConnectionError(f"Failed to connect to VLLM at {self.llm_endpoint}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during VLLM validation: {e}")
            raise

    async def _rewrite_query(
        self,
        query: str,
        history: Optional[List[PrevQuestionDetails]],
        max_new_tokens: int,
        temperature: float,
    ) -> str:
        """Rewrite query in a single LLM call — contextualizes with history if available, and refines."""
        if history:
            formatted_history = self._format_history(history)
            history_turns = min(len(history), 3)
            logger.info(
                f"[REWRITE] Input: '{query}' with {history_turns} history turns"
            )
            user_prompt = QUERY_REWRITE_WITH_HISTORY_USER_PROMPT.format(
                history=formatted_history, question=query
            )

            response = await self._call_llm(
                QUERY_REWRITE_WITH_HISTORY_SYSTEM_PROMPT, user_prompt, max_new_tokens, temperature
            )

        else:
            logger.info(f"[REWRITE] Input: '{query}' (no history)")
            user_prompt = QUERY_REWRITE_USER_PROMPT.format(question=query)

            response = await self._call_llm(
                QUERY_REWRITE_SYSTEM_PROMPT, user_prompt, max_new_tokens, temperature
            )

        rewritten = self._clean_llm_response(response, fallback=query)
        logger.info(f"[REWRITE] Output: '{query}' -> '{rewritten}'")
        return rewritten

    def _clean_llm_response(self, text: str, fallback: str = "") -> str:
        """Clean up LLM response by removing quotes and numbering.

        Args:
            text: Raw LLM response
            fallback: Value to return if cleaned text is empty
        """
        if not text:
            return fallback

        cleaned = text.strip()
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (
            cleaned.startswith("'") and cleaned.endswith("'")
        ):
            cleaned = cleaned[1:-1]
        cleaned = re.sub(r"^[\d]+[\.\)]\s*", "", cleaned)
        cleaned = re.sub(r"^-+\s+", "", cleaned)
        cleaned = cleaned.strip()

        return cleaned if cleaned else fallback

    async def run(
        self,
        input: TextDoc,
        access_token: str = "",
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> TextDoc:
        """Run query rewriting pipeline.

        Rewrites the query in a single LLM call. If history_id is present,
        the query is contextualized with chat history and refined at once.

        Args:
            input: Input TextDoc with query text
            access_token: Authorization token for chat history service
            max_new_tokens: Maximum tokens for LLM response (from fingerprint or default)
            temperature: Temperature for LLM generation (from fingerprint or default)
        """
        start_time = time.time()

        max_new_tokens = max_new_tokens if max_new_tokens is not None else self.DEFAULT_MAX_NEW_TOKENS
        temperature = (
            temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        )

        original_query = input.text
        original_metadata = input.metadata or {}

        logger.info(f"[RUN] Original query: '{original_query}', history_id: {input.history_id or 'None'}")
        logger.debug(f"[RUN] max_new_tokens: {max_new_tokens}, temperature: {temperature}")

        try:
            async with asyncio.timeout(self.timeout):
                async with self.semaphore:
                    history = None

                    if input.history_id:
                        history = await self._get_chat_history(
                            input.history_id, access_token
                        )
                        if history:
                            logger.debug(
                                f"[RUN] Got {len(history)} history items"
                            )

                    logger.debug("[RUN] Rewriting query...")
                    rewritten_query = await self._rewrite_query(
                        original_query, history if history else None,
                        max_new_tokens, temperature,
                    )

                    elapsed = time.time() - start_time
                    logger.info(
                        f"[RUN] Query rewrite done in {elapsed:.2f}s: '{original_query}' -> '{rewritten_query}'"
                    )

                    return TextDoc(
                        text=rewritten_query,
                        original_query=original_query,
                        history_id=input.history_id,
                        metadata={
                            **original_metadata,
                            "original_query": original_query,
                            "rewritten": True,
                        },
                    )

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.warning(
                f"[RUN] TIMEOUT after {elapsed:.2f}s (limit: {self.timeout}s)"
            )
            return TextDoc(
                text=original_query,
                original_query=original_query,
                history_id=input.history_id,
                metadata={**original_metadata, "rewrite_timeout": True},
            )

    async def close(self):
        """Cleanup resources."""
        await self._http_client.aclose()
