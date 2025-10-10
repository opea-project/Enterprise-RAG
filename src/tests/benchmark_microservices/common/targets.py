import json
import logging
import re
import time
from abc import ABC, abstractmethod

import aiohttp
from aiohttp import ClientResponse

from src.tests.benchmark_microservices.common.structures import (
    BenchmarkParams,
    RequestTimings,
    StreamRequestTimings,
)

logger = logging.getLogger(__name__)


class BenchTarget(ABC):
    """Handles target-specific parts of requests.

    That includes things like shape of request, handling specific response format etc.
    """

    REQUEST_HEADERS = {"Content-Type": "application/json"}
    _RESPONSE_REGEX = None  # Override in child class

    def __init__(
        self, model_name: str, question: str, benchmark_params: BenchmarkParams
    ):
        self._model_name = model_name
        self._question = question
        self._benchmark_params = benchmark_params

    @abstractmethod
    def request_body(self) -> dict:
        pass

    async def call_service(self, url: str, request_body: dict) -> RequestTimings:
        """Executes request.

        :param url: Request target
        :param request_body: HTTP request body
        :return: Request timings
        """
        data = json.dumps(request_body)

        timings = RequestTimings()

        timings.start = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, data=data, headers=self.REQUEST_HEADERS
            ) as response_handler:
                await response_handler.read()
        timings.end = time.perf_counter()

        return timings

    async def call_service_streaming(
        self, url: str, request_body: dict
    ) -> StreamRequestTimings:
        """Executes request with streaming response.

        :param url: Request target
        :param request_body: HTTP request body
        :return: Request timings down to single tokens
        """
        data = json.dumps(request_body)
        timings = StreamRequestTimings()
        timings.start = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, data=data, headers=self.REQUEST_HEADERS
            ) as response_handler:
                await self._streaming_collector(response_handler, timings)
        timings.end = time.perf_counter()

        return timings

    async def _streaming_collector(
        self, response_handler: ClientResponse, timings: StreamRequestTimings
    ):
        """Collects tokens from response handler and saves timings (model server).

        :param ClientResponse response_handler: Object to get stream response from
        :param StreamRequestTimings timings: Timings object to fill with tokens timings
        """
        answer = ""

        time_this = timings.start
        async for data in response_handler.content:
            line = data.decode("unicode_escape")
            match = self._RESPONSE_REGEX.search(line)
            if match:
                try:
                    word = self._chunk_extract(match)
                    time_last = time_this
                    time_this = time.perf_counter()
                    timings.token_timings.append(time_this - time_last)
                    answer += word
                except ValueError:
                    logging.warning(f"Found irregular data: {line}")

    @abstractmethod
    def _chunk_extract(self, regex_match) -> str:
        pass


class LlmMicroserviceBenchTarget(BenchTarget):
    _RESPONSE_REGEX = re.compile(r"'(.+)'")

    def request_body(self) -> dict:
        return {
            "query": self._question,
            "max_new_tokens": self._benchmark_params.max_new_tokens,
            "top_k": 10,
            "top_p": 0.95,
            "typical_p": 0.95,
            "temperature": 0,
            "repetition_penalty": 1.03,
            "stream": self._benchmark_params.streaming,
            # "do_sample": False  # Makes fixed answer length
        }

    def _chunk_extract(self, regex_match) -> str:
        word = regex_match.group(1)
        return word


class VllmBenchTarget(BenchTarget):
    _RESPONSE_REGEX = re.compile(r"({.+})")

    def request_body(self) -> dict:
        return {
            "model": self._model_name,
            "prompt": self._question,
            "max_tokens": self._benchmark_params.max_new_tokens,
            "min_tokens": self._benchmark_params.max_new_tokens,  # enforce same tokens num
            "temperature": 0,
            "stream": self._benchmark_params.streaming,
        }

    def _chunk_extract(self, regex_match) -> str:
        chunk = json.loads(regex_match.group(1))
        word = chunk["choices"][0]["text"]
        return word
