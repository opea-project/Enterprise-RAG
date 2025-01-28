import asyncio
import csv
import datetime
import itertools
import json
import logging
import operator
import re
import time
from abc import abstractmethod
from functools import partial
from typing import NamedTuple, Type

import aiohttp
import numpy as np
from transformers import AutoTokenizer

from src.tests.docker_setups.base import LLMsDockerSetup

logger = logging.getLogger(__name__)


# Non-docker-related benchmark parameters. Subject for further refactor to include Docker conf too.
class BenchmarkParams(NamedTuple):
    streaming: bool
    service: str
    input_token_num: int
    max_new_tokens: int
    num_burst_requests: int


class RequestTimings:
    def __init__(self):
        self.start = 0
        self.end = 0

    @property
    def overall(self) -> float:
        return self.end - self.start


class StreamRequestTimings(RequestTimings):
    def __init__(self):
        super().__init__()
        self.token_timings = []

    @property
    def first_token_time(self) -> float:
        return self.token_timings[0]

    @property
    def second_to_last_timings(self) -> list[float]:
        return self.token_timings[1:]

    @property
    def second_to_last_total_time(self) -> float:
        return sum(self.second_to_last_timings)

    @property
    def num_tokens(self) -> int:
        return len(self.token_timings)


class BenchmarkRecordResults:
    """Summary stats for burst results."""

    def __init__(self, benchmark_params: BenchmarkParams):
        self._benchmark_params = benchmark_params
        self._requests_results_set = []

    def add_request_results(self, timings: list):
        """Add timings of a requests burst."""
        self._requests_results_set += timings

    @property
    def total_time_avg(self) -> float:
        """Average processing time of a requests."""
        total_time_timings = [res.overall for res in self._requests_results_set]
        return float(np.average(total_time_timings))

    @property
    def received_tokens_avg(self) -> int:
        """Average number of received tokens in responses."""
        responses_tokens_numbers = [
            res.num_tokens for res in self._requests_results_set
        ]
        return int(np.average(responses_tokens_numbers))

    @property
    def total_time_p50(self) -> float:
        """P50 percentile processing times of a requests."""
        total_time_timings = [res.overall for res in self._requests_results_set]
        return float(np.percentile(total_time_timings, 50))

    @property
    def total_time_p90(self) -> float:
        """P90 percentile processing times of a requests."""
        total_time_timings = [res.overall for res in self._requests_results_set]
        return float(np.percentile(total_time_timings, 90))

    @property
    def total_time_p99(self) -> float:
        """P90 percentile processing times of a requests."""
        total_time_timings = [res.overall for res in self._requests_results_set]
        return float(np.percentile(total_time_timings, 99))


class StreamBenchmarkRecordResults(BenchmarkRecordResults):
    @property
    def first_token_avg(self) -> float:
        """Average processing time of the first tokens."""
        first_token_timings = [
            res.first_token_time for res in self._requests_results_set
        ]
        return float(np.average(first_token_timings))

    @property
    def prefill_throughput_avg(self) -> int:
        """Average throughput of prefill."""
        prefill_throughputs = [
            self._benchmark_params.input_token_num / res.first_token_time
            for res in self._requests_results_set
        ]
        return int(np.average(prefill_throughputs))

    @property
    def decode_throughput_avg(self) -> int:
        """Average throughput of decode."""
        decode_throughputs = [
            (self._benchmark_params.max_new_tokens / res.second_to_last_total_time)
            for res in self._requests_results_set
        ]
        return int(np.average(decode_throughputs))

    @property
    def all_second_to_last_timings(self) -> list[float]:
        return list(
            itertools.chain.from_iterable(
                [res.second_to_last_timings for res in self._requests_results_set]
            )
        )

    @property
    def second_plus_avg(self) -> float:
        """Average processing time of a 2nd+ token."""
        return float(np.average(self.all_second_to_last_timings))

    @property
    def second_plus_p50(self) -> float:
        """P50 percentile processing time of a 2nd+ token."""
        return float(np.percentile(self.all_second_to_last_timings, 50))

    @property
    def second_plus_p90(self) -> float:
        """P90 percentile processing time of a 2nd+ token."""
        return float(np.percentile(self.all_second_to_last_timings, 90))

    @property
    def second_plus_p99(self) -> float:
        """P99 percentile processing time of a 2nd+ token."""
        return float(np.percentile(self.all_second_to_last_timings, 99))


def format_float(value, precision) -> str:
    if isinstance(value, float):
        return f"{value:.{precision}f}"
    return value


class BenchmarkBase:
    RESULTS_FIELDS_NAMES_BASE = [
        "service",
        "streaming",
        "input_token_num",
        "max_new_tokens",
        "num_burst_requests",
        "total_time_avg",
        "total_time_p50",
        "total_time_p90",
        "total_time_p99",
        "received_tokens_avg",
        "first_token_avg",
        "prefill_throughput_avg",
        "decode_throughput_avg",
        "second+_avg",
        "second+_p50",
        "second+_p90",
        "second+_p99",
        "notes",
    ]

    REQUEST_HEADERS = {"Content-Type": "application/json"}

    def __init__(
        self, setup_combinations, parameters_combinations, model_based_token_sizes=None
    ):
        self._setup_combinations = setup_combinations
        self._parameters_combinations = parameters_combinations
        self._model_base_token_sizes = (
            model_based_token_sizes if model_based_token_sizes else []
        )
        self._results = []

    @property
    @abstractmethod
    def _DOCKER_SETUP_CLASS(self) -> Type[LLMsDockerSetup]:
        pass

    @property
    @abstractmethod
    def _fields_names(self) -> list[str]:
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    async def run_multiple_requests(
        self,
        service: str,
        model: str,
        text: str,
        streaming: bool,
        max_new_tokens: int,
        times: int,
    ) -> list[StreamRequestTimings]:
        """Executes burst requests to given service"""
        pass

    def vllm_request_body(self, max_new_tokens, model, question, streaming) -> dict:
        return {
            "model": model,
            "prompt": question,
            "max_tokens": max_new_tokens,
            "min_tokens": max_new_tokens,  # enforce same tokens num
            "temperature": 0,
            "stream": streaming,
        }

    def save_results_as_csv(self, file_name):
        now = datetime.datetime.now()
        formatted_datetime = now.strftime("%Y-%m-%d %H-%M-%S")
        with open(f"/tmp/{formatted_datetime} {file_name}", "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self._fields_names)
            writer.writeheader()
            for row in self._results:
                formatted_row = {
                    key: format_float(value, 3) for key, value in row.items()
                }
                writer.writerow(formatted_row)

    def _extended_combinations(self, model_context_window: int) -> list[dict]:
        """Extended benchmark parameters based on model context window.

        This functions extends combinations basing on:
        - model context window size
        - provided partial functions that does size manipulations

        For example:
        If `manipulation` is add(-1), executing this manipulation on model size of 1024
        will return 1024 - 1 = 1023
        """

        extra_input_token_sizes = [
            int(manipulation(model_context_window))
            for manipulation in self._model_base_token_sizes
        ]

        parameters_combinations = self._parameters_combinations.copy()

        new_combinations = []
        for comb in parameters_combinations:
            for token_size in extra_input_token_sizes:
                new_parameters = comb.copy()
                new_parameters["input_token_num"] = token_size
                new_combinations.append(new_parameters)

        parameters_combinations.extend(new_combinations)
        logger.info(
            f"Extended benchmark parameters by following {len(extra_input_token_sizes)} input_token_nums based on model size ({model_context_window}):"
        )
        logger.info(extra_input_token_sizes)
        return parameters_combinations

    def execute_scenario(self, model_name: str, input_params: BenchmarkParams) -> dict:
        """Collects one record of benchmark.

        This function executes benchmark with given parameters, running on already prepared docker deployment.
        """
        streaming = input_params.streaming
        service = input_params.service
        max_new_tokens = input_params.max_new_tokens
        input_token_num = input_params.input_token_num
        num_burst_requests = input_params.num_burst_requests
        notes = ""

        logger.debug(
            f"Collect benchmark record with: {service=} {max_new_tokens=} {input_token_num=} {num_burst_requests=}"
        )

        # config = AutoConfig.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        text = ""
        with open("src/tests/benchmark/llms/tokenizer_input.txt", "r") as input_file:
            text = input_file.read()

        input_tokens = tokenizer.encode(text)[:input_token_num]
        assert len(input_tokens) == input_token_num

        prompt = tokenizer.decode(input_tokens)

        requests_timings = asyncio.run(
            self.run_multiple_requests(
                service,
                model_name,
                prompt,
                streaming,
                max_new_tokens,
                num_burst_requests,
            )
        )

        benchmark_results = {
            "service": service,
            "streaming": streaming,
            "input_token_num": input_token_num,
            "max_new_tokens": max_new_tokens,
            "num_burst_requests": num_burst_requests,
            "received_tokens_avg": 0,
            "first_token_avg": 0,
            "prefill_throughput_avg": 0,
            "decode_throughput_avg": 0,
            "total_time_avg": 0,
            "total_time_p50": 0,
            "total_time_p90": 0,
            "total_time_p99": 0,
            "second+_avg": 0,
            "second+_p50": 0,
            "second+_p90": 0,
            "second+_p99": 0,
            "notes": "",
        }

        correct_timings = [t for t in requests_timings if not isinstance(t, Exception)]
        if len(requests_timings) != len(correct_timings):
            errored = len(requests_timings) - len(correct_timings)
            msg = f"{errored} requests has failed!"
            logger.warning(msg)
            notes += msg
            benchmark_results["notes"] = notes
            if len(correct_timings) == 0:
                logger.warning(
                    "No request succeeded, nothing to do here. Return empty row."
                )
                benchmark_results["notes"] = notes
                return benchmark_results

        if input_params.streaming is True:
            results = fill_results_streaming(
                input_params, benchmark_results, correct_timings
            )
        else:
            results = fill_results_nonstreaming(
                input_params, benchmark_results, correct_timings
            )

        return results

    async def call_modelserver(
        self, server, model, question, max_new_tokens, streaming, wid
    ) -> StreamRequestTimings:
        headers = {"Content-Type": "application/json"}
        request_body = self.vllm_request_body(
            max_new_tokens, model, question, streaming
        )
        data = json.dumps(request_body)

        url = f"http://{server}/v1/completions"

        if streaming is True:
            timings = StreamRequestTimings()
        else:
            timings = RequestTimings()

        # TODO: Refactor it so as to collect additional timings for streaming
        timings.start = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, data=data, headers=headers
            ) as response_handler:
                if streaming is True:
                    timings = await self._streaming_collector(
                        response_handler, timings, wid
                    )
                else:
                    timings = await self._nonstreaming_collector(
                        response_handler, timings, wid
                    )
        timings.end = time.perf_counter()

        return timings

    async def _streaming_collector(
        self, response_handler, timings, wid
    ) -> StreamRequestTimings:
        reg = re.compile(r"({.+})")
        answer = ""

        time_this = timings.start
        counter = 1
        async for chunk in response_handler.content:
            line = chunk.decode("unicode_escape")
            match = reg.search(line)
            if match:
                try:
                    chunk = json.loads(match.group(1))
                    word = chunk["choices"][0]["text"]
                    time_last = time_this
                    time_this = time.perf_counter()
                    timings.token_timings.append(time_this - time_last)
                    if counter < 4:
                        logger.debug(
                            f"[#{wid}] extracted {counter}. {word=} ({time_this - time_last:3.2f} s)"
                        )
                    answer += word
                    counter += 1
                except ValueError:
                    logging.info(f"[#{wid}] A: {line}")
                    if line == "data: [DONE]":
                        logging.info(f"[#{wid}] Found [DONE]")
                        break
        return timings

    async def _nonstreaming_collector(
        self, response_handler, timings, wid
    ) -> RequestTimings:
        data = await response_handler.read()
        logger.debug(f"[#{wid}] extracted  {data=}")
        return timings


def fill_results_streaming(input_params, benchmark_results, correct_timings) -> dict:
    max_new_tokens = input_params.max_new_tokens
    num_burst_requests = input_params.num_burst_requests
    results = StreamBenchmarkRecordResults(input_params)
    for timings in correct_timings:
        if timings.num_tokens != max_new_tokens:
            logger.warning(
                f"Max new tokens is {max_new_tokens}, but {timings.num_tokens} received."
            )
            if timings.num_tokens > max_new_tokens:
                logger.error("Num tokens received exceeds max_new_tokens!")

    results.add_request_results(correct_timings)

    benchmark_results["received_tokens_avg"] = results.received_tokens_avg
    benchmark_results["first_token_avg"] = results.first_token_avg
    benchmark_results["prefill_throughput_avg"] = results.prefill_throughput_avg
    benchmark_results["decode_throughput_avg"] = results.decode_throughput_avg
    benchmark_results["total_time_avg"] = results.total_time_avg
    benchmark_results["total_time_p50"] = results.total_time_p50
    benchmark_results["total_time_p90"] = results.total_time_p90
    benchmark_results["total_time_p99"] = results.total_time_p99
    benchmark_results["second+_avg"] = results.second_plus_avg
    benchmark_results["second+_p50"] = results.second_plus_p50
    benchmark_results["second+_p90"] = results.second_plus_p90
    benchmark_results["second+_p99"] = results.second_plus_p99

    logger.info("| reqs | tokens avg | total time avg | first avg | 2nd to last avg |")
    logger.info(
        f"| {num_burst_requests:03}  "
        f"|  {benchmark_results['received_tokens_avg']:4.1f}    "
        f"|     {benchmark_results['total_time_avg']:6.3f}    "
        f"|  {benchmark_results['first_token_avg']:6.3f}   "
        f"|      {benchmark_results['second+_avg']:4.3f}      |"
    )

    return benchmark_results


def fill_results_nonstreaming(input_params, benchmark_results, correct_timings) -> dict:
    results = BenchmarkRecordResults(input_params)
    results.add_request_results(correct_timings)

    benchmark_results["total_time_avg"] = results.total_time_avg
    benchmark_results["total_time_p50"] = results.total_time_p50
    benchmark_results["total_time_p90"] = results.total_time_p90
    benchmark_results["total_time_p99"] = results.total_time_p99

    logger.info("Non-stream requests stats")
    logger.info("|   avg  |   p50  |   p90  |   p99  |")
    logger.info(
        f"| {benchmark_results['total_time_avg']:6.2f} "
        f"| {benchmark_results['total_time_p50']:6.2f} "
        f"| {benchmark_results['total_time_p90']:6.2f} "
        f"| {benchmark_results['total_time_p99']:6.2f} |"
    )

    return benchmark_results


def context_size_add(value) -> partial:
    return partial(operator.add, value)


def context_size_mul(value) -> partial:
    return partial(operator.mul, value)


def generate_combinations(d) -> list[dict]:
    """Cartesian product of dict with values specified as lists."""

    def recurse(d):
        if isinstance(d, dict):
            keys, values = zip(*d.items())
            combinations = [
                dict(zip(keys, v))
                for v in itertools.product(*(recurse(v) for v in values))
            ]
            return combinations
        elif isinstance(d, list):
            return d
        else:
            return [d]

    return recurse(d)
