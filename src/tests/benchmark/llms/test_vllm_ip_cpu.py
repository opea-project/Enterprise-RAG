import asyncio
import json
import logging
import re
import time
from abc import abstractmethod
from typing import Type

import aiohttp
from transformers import AutoConfig

from src.tests.benchmark.common.structures import (
    BenchmarkBase,
    BenchmarkParams,
    StreamRequestTimings,
    context_size_add,
    context_size_mul,
    generate_combinations,
)
from src.tests.docker_setups.llms.vllm_ip_cpu import (
    LLMs_VllmIP_CPU_EnvKeys,
    LLMsVllmIP_CPU_DockerSetup,
)

logger = logging.getLogger(__name__)


class VllmIpexCpuBenchmark(BenchmarkBase):
    def run(self):
        for i, setup in enumerate(self._setup_combinations):
            logger.debug(f"Deploying {i + 1}/{len(self._setup_combinations)} setup")
            dockers = self._DOCKER_SETUP_CLASS(
                "comps/llms/impl/model_server/vllm/docker/.env.cpu",
                setup["config_override"],
                setup["config_extra"],
                setup["docker_extra"],
            )
            dockers.deploy()

            model_name = dockers.get_docker_env(
                LLMs_VllmIP_CPU_EnvKeys.LLM_VLLM_MODEL_NAME
            )
            config = AutoConfig.from_pretrained(model_name)
            context_window = config.sliding_window

            parameters_combinations = self._extended_combinations(context_window)
            parameters_combinations = [
                BenchmarkParams(**options) for options in parameters_combinations
            ]

            for j, input_params in enumerate(parameters_combinations):
                logger.debug(f"Running {j + 1}/{len(parameters_combinations)} case")
                logger.debug(
                    f"Including setups: {i * len(parameters_combinations) + j + 1}/{len(parameters_combinations) * len(self._setup_combinations)} case"
                )

                results = self.execute_scenario(
                    model_name, input_params
                )  # add model-related  params

                for k, v in setup["config_override"].items():
                    results[k] = v

                for k, v in setup["config_extra"].items():
                    results[k] = v

                for k, v in setup["docker_extra"].items():
                    results[k] = v

                self._results.append(results)

    async def run_multiple_requests(
        self,
        service: str,
        model: str,
        text: str,
        streaming: bool,
        max_new_tokens: int,
        times: int,
    ) -> list[StreamRequestTimings]:
        functable = {
            "model_server": {
                "func": self.call_modelserver,
                "url": f"localhost:{self._DOCKER_SETUP_CLASS.INTERNAL_COMMUNICATION_PORT}",
            },
            "microservice": {
                "func": call_microservice,
                "url": f"localhost:{self._DOCKER_SETUP_CLASS.MICROSERVICE_API_PORT}",
            },
        }
        tasks = [
            functable[service]["func"](
                functable[service]["url"], model, text, max_new_tokens, streaming, n
            )
            for n in range(times)
        ]
        objs = await asyncio.gather(*tasks, return_exceptions=True)
        return objs

    @property
    def _fields_names(self) -> list[str]:
        fields_names = self.RESULTS_FIELDS_NAMES_BASE.copy()

        fields_names = [
            key for key in SETUP_CONFIGURATIONS["config_override"]
        ] + fields_names
        fields_names = [
            key for key in SETUP_CONFIGURATIONS["config_extra"]
        ] + fields_names
        fields_names = [
            key for key in SETUP_CONFIGURATIONS["docker_extra"]
        ] + fields_names

        return fields_names

    @property
    @abstractmethod
    def _DOCKER_SETUP_CLASS(self) -> Type[LLMsVllmIP_CPU_DockerSetup]:
        return LLMsVllmIP_CPU_DockerSetup


async def call_microservice(
    server, question, max_new_tokens, wid
) -> StreamRequestTimings:
    logger.debug(f"Starting async task #{wid}")
    headers = {"Content-Type": "application/json"}
    request_body = {
        "query": question,
        "max_new_tokens": max_new_tokens,
        "top_k": 10,
        "top_p": 0.95,
        "typical_p": 0.95,
        "temperature": 0,
        "repetition_penalty": 1.03,
        "streaming": True,
        # "do_sample": False  # Makes fixed answer length
    }
    data = json.dumps(request_body)
    timings = StreamRequestTimings()

    timings.start = time.perf_counter()
    time_this = timings.start

    url = f"http://{server}/v1/chat/completions"
    reg = re.compile("data: '(.+?)'")
    answer = ""

    logger.debug("Before sending request")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as response:
            if response.status != 200:
                logger.error(f"Received response {str(response.status)}")
            async for chunk in response.content:
                line = chunk.decode("unicode_escape")
                match = reg.match(line)
                if match:
                    chunk = match.group(1)
                    time_last = time_this
                    time_this = time.perf_counter()
                    timings.token_timings.append(time_this - time_last)
                    answer += chunk
                    # logging.debug(f"[#{wid}] A: {chunk}")
                if line == "data: [DONE]":
                    logging.info(f"[#{wid}] Found [DONE]")
                    break

    logger.info(f"Grabbed answer: {answer}")
    timings.end = time.perf_counter()
    return timings


SETUP_CONFIGURATIONS = {
    "config_override": {
        LLMs_VllmIP_CPU_EnvKeys.VLLM_TP_SIZE.value: 1,
    },
    "config_extra": {
        "VLLM_CPU_OMP_THREADS_BIND": ["0-15"],
    },
    "docker_extra": {
        "cpuset_mems": [[0]],
        "privileged": True,
    },
}

GENERAL_BENCHMARK_PARAMETERS = {
    "service": ["model_server"],
    "streaming": [True],
    "num_burst_requests": [1],
    "input_token_num": [1024],
    "max_new_tokens": [1024],
}

MODEL_RELATED_TOKEN_NUMS = [
    context_size_add(-1),
    context_size_mul(0.5),
]


def test_pytest_stream():
    setup_combinations = generate_combinations(SETUP_CONFIGURATIONS)
    parameters_combinations = generate_combinations(GENERAL_BENCHMARK_PARAMETERS)

    benchmark = VllmIpexCpuBenchmark(
        setup_combinations, parameters_combinations, MODEL_RELATED_TOKEN_NUMS
    )

    benchmark.run()
    benchmark.save_results_as_csv("benchmark_results_stream.csv")
