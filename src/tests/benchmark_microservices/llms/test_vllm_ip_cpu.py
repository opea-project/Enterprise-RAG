import asyncio
import json
import logging
import os
import re
import time
from abc import abstractmethod
from typing import Type

import aiohttp
from transformers import AutoConfig

from src.tests.benchmark_microservices.common.structures import (
    BenchmarkBase,
    BenchmarkParams,
    StreamRequestTimings,
    generate_combinations,
)
from src.tests.benchmark_microservices.common.targets import (
    VllmBenchTarget,
    LlmMicroserviceBenchTarget,
)
from src.tests.docker_setups.llms.vllm_ip_cpu import (
    LLMs_VllmIP_CPU_EnvKeys,
    LLMsVllmIP_CPU_DockerSetup,
)

from os.path import dirname, abspath

logger = logging.getLogger(__name__)
os.chdir(dirname(dirname(dirname(dirname(dirname(abspath(__file__)))))))


class VllmIpexCpuBenchmark(BenchmarkBase):
    def run(self):
        for i, setup in enumerate(self._setup_combinations):
            logger.debug(f"Deploying {i + 1}/{len(self._setup_combinations)} setup")
            dockers = self._DOCKER_SETUP_CLASS(
                "comps/llms/impl/model_server/vllm/docker/.env.cpu",
                setup["config_override"],
                custom_microservice_envs=setup["config_microservice_extra"],
                custom_model_server_envs=setup["config_model_server_extra"],
                custom_model_server_docker_params=setup["docker_model_server_extra"],
            )
            dockers.deploy()

            model_name = dockers.get_docker_env(
                LLMs_VllmIP_CPU_EnvKeys.LLM_VLLM_MODEL_NAME
            )
            config = AutoConfig.from_pretrained(model_name)
            context_window = config.max_position_embeddings

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

                if setup["config_override"]:
                    for k, v in setup["config_override"].items():
                        results[k] = v

                if setup["config_microservice_extra"]:
                    for k, v in setup["config_microservice_extra"].items():
                        results[k] = v

                if setup["config_model_server_extra"]:
                    for k, v in setup["config_model_server_extra"].items():
                        results[k] = v

                if setup["docker_model_server_extra"]:
                    for k, v in setup["docker_model_server_extra"].items():
                        results[k] = v

                self._results.append(results)

    async def run_multiple_requests(
        self, model: str, question: str, params: BenchmarkParams
    ) -> list[StreamRequestTimings]:
        if params.service == "model_server":
            url = f"http://localhost:{self._DOCKER_SETUP_CLASS.INTERNAL_COMMUNICATION_PORT}/v1/completions"
            target = VllmBenchTarget(model, question, params)

        elif params.service == "microservice":
            url = f"http://localhost:{self._DOCKER_SETUP_CLASS.MICROSERVICE_API_PORT}/v1/chat/completions"
            target = LlmMicroserviceBenchTarget(model, question, params)
        else:
            raise ValueError(
                "Incorrect `service` parameter. Valid values are `model_server` and `microservice`"
            )

        request_body = target.request_body()

        if params.streaming:
            tasks = [
                target.call_service_streaming(url, request_body)
                for _ in range(params.num_burst_requests)
            ]
        else:
            tasks = [
                target.call_service(url, request_body)
                for _ in range(params.num_burst_requests)
            ]

        objs = await asyncio.gather(*tasks, return_exceptions=True)
        return objs

    @property
    def _fields_names(self) -> list[str]:

        fields_names = []

        # Combinations are list of dicts, therefore pick keys from 1st of kind
        if self._setup_combinations[0]["config_override"]:
            fields_names += [key for key in self._setup_combinations[0]["config_override"]]

        if self._setup_combinations[0]["config_microservice_extra"]:
            fields_names += [
                key for key in self._setup_combinations[0]["config_microservice_extra"]
            ]

        if self._setup_combinations[0]["config_model_server_extra"]:
            fields_names += [
                key for key in self._setup_combinations[0]["config_model_server_extra"]
            ]

        if self._setup_combinations[0]["docker_model_server_extra"]:
            fields_names += [
                key for key in self._setup_combinations[0]["docker_model_server_extra"]
            ]

        fields_names += self.RESULTS_FIELDS_NAMES_BASE.copy()

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
        "stream": True,
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


def test_vllm_ip_cpu():
    yaml_conf = VllmIpexCpuBenchmark.parse_yaml_config('src/tests/benchmark_microservices/config_defaults/vllm_ip_cpu.yaml')
    setup_combinations = generate_combinations(yaml_conf["setup_configurations"])
    parameters_combinations = generate_combinations(yaml_conf["benchmark_parameters"])
    model_related_token_nums = yaml_conf["model_related_token_nums"]

    benchmark = VllmIpexCpuBenchmark(
        setup_combinations, parameters_combinations, model_related_token_nums
    )

    benchmark.run()
    benchmark.save_results_as_csv("benchmark_results.csv")
