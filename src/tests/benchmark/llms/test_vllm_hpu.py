import asyncio
import logging
from abc import abstractmethod
from typing import Type

from transformers import AutoConfig

from src.tests.benchmark.common.structures import (
    BenchmarkBase,
    BenchmarkParams,
    StreamRequestTimings,
    context_size_mul,
    generate_combinations,
)
from src.tests.docker_setups.llms.vllm_hpu import (
    LLMs_VLLM_HPU_EnvKeys,
    LLMsVllm_HPU_DockerSetup,
)

logger = logging.getLogger(__name__)


class VllmHpuBenchmark(BenchmarkBase):
    def run(self):
        for i, setup in enumerate(self._setup_combinations):
            logger.debug(f"Deploying {i + 1}/{len(self._setup_combinations)} setup")
            try:
                dockers = self._DOCKER_SETUP_CLASS(
                    "comps/llms/impl/model_server/vllm/docker/.env.hpu",
                    setup["config_override"],
                    setup["config_extra"],
                    setup["docker_extra"],
                )
                dockers.deploy()

                model_name = dockers.get_docker_env(
                    LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME
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

            except RuntimeError:
                logger.error("Docker setup failed! Continue with next setup...")
                continue

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
            key for key in HARDCODED_SETUP_CONFIGURATIONS[0]["config_override"]
        ] + fields_names
        fields_names = [
            key for key in HARDCODED_SETUP_CONFIGURATIONS[0]["config_extra"]
        ] + fields_names
        fields_names = [
            key for key in HARDCODED_SETUP_CONFIGURATIONS[0]["docker_extra"]
        ] + fields_names

        return fields_names

    @property
    @abstractmethod
    def _DOCKER_SETUP_CLASS(self) -> Type[LLMsVllm_HPU_DockerSetup]:
        return LLMsVllm_HPU_DockerSetup


SETUP_CONFIGURATIONS = {
    "config_override": {
        # LLMs_VLLM_HPU_EnvKeys.VLLM_TP_SIZE.value: [8]
    },
    "config_extra": {},
    "docker_extra": {},
}

"""
Because 3 parameters are related to each other:
- HABANA_VISIBLE_DEVICES
- VLLM_TP_SIZE
- NUM_SHARDS

Combinations generator requires further development, with filters for example.
As of now this sort of config sets can be defined manually.
"""
HARDCODED_SETUP_CONFIGURATIONS = [
    {
        "config_override": {
            LLMs_VLLM_HPU_EnvKeys.HABANA_VISIBLE_DEVICES.value: "0",
            LLMs_VLLM_HPU_EnvKeys.NUM_SHARD.value: 1,
            LLMs_VLLM_HPU_EnvKeys.VLLM_TP_SIZE.value: 1,
            LLMs_VLLM_HPU_EnvKeys.SHARDED.value: "false",
            LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x7B-Instruct-v0.1",
        },
        "config_extra": {},
        "docker_extra": {},
    },
    {
        "config_override": {
            LLMs_VLLM_HPU_EnvKeys.HABANA_VISIBLE_DEVICES.value: "0",
            LLMs_VLLM_HPU_EnvKeys.NUM_SHARD.value: 1,
            LLMs_VLLM_HPU_EnvKeys.VLLM_TP_SIZE.value: 1,
            LLMs_VLLM_HPU_EnvKeys.SHARDED.value: "false",
            LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x22B-Instruct-v0.1",
        },
        "config_extra": {},
        "docker_extra": {},
    },
    {
        "config_override": {
            LLMs_VLLM_HPU_EnvKeys.HABANA_VISIBLE_DEVICES.value: "0,1",
            LLMs_VLLM_HPU_EnvKeys.NUM_SHARD.value: 2,
            LLMs_VLLM_HPU_EnvKeys.VLLM_TP_SIZE.value: 2,
            LLMs_VLLM_HPU_EnvKeys.SHARDED.value: "true",
            LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x7B-Instruct-v0.1",
        },
        "config_extra": {},
        "docker_extra": {},
    },
    {
        "config_override": {
            LLMs_VLLM_HPU_EnvKeys.HABANA_VISIBLE_DEVICES.value: "0,1",
            LLMs_VLLM_HPU_EnvKeys.NUM_SHARD.value: 2,
            LLMs_VLLM_HPU_EnvKeys.VLLM_TP_SIZE.value: 2,
            LLMs_VLLM_HPU_EnvKeys.SHARDED.value: "true",
            LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x22B-Instruct-v0.1",
        },
        "config_extra": {},
        "docker_extra": {},
    },
    {
        "config_override": {
            LLMs_VLLM_HPU_EnvKeys.HABANA_VISIBLE_DEVICES.value: "0,1,2,3",
            LLMs_VLLM_HPU_EnvKeys.NUM_SHARD.value: 4,
            LLMs_VLLM_HPU_EnvKeys.VLLM_TP_SIZE.value: 4,
            LLMs_VLLM_HPU_EnvKeys.SHARDED.value: "true",
            LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x7B-Instruct-v0.1",
        },
        "config_extra": {},
        "docker_extra": {},
    },
    {
        "config_override": {
            LLMs_VLLM_HPU_EnvKeys.HABANA_VISIBLE_DEVICES.value: "0,1,2,3",
            LLMs_VLLM_HPU_EnvKeys.NUM_SHARD.value: 4,
            LLMs_VLLM_HPU_EnvKeys.VLLM_TP_SIZE.value: 4,
            LLMs_VLLM_HPU_EnvKeys.SHARDED.value: "true",
            LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x22B-Instruct-v0.1",
        },
        "config_extra": {},
        "docker_extra": {},
    },
    {
        "config_override": {
            LLMs_VLLM_HPU_EnvKeys.HABANA_VISIBLE_DEVICES.value: "all",
            LLMs_VLLM_HPU_EnvKeys.NUM_SHARD.value: 8,
            LLMs_VLLM_HPU_EnvKeys.VLLM_TP_SIZE.value: 8,
            LLMs_VLLM_HPU_EnvKeys.SHARDED.value: "true",
            LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x7B-Instruct-v0.1",
        },
        "config_extra": {},
        "docker_extra": {},
    },
    {
        "config_override": {
            LLMs_VLLM_HPU_EnvKeys.HABANA_VISIBLE_DEVICES.value: "all",
            LLMs_VLLM_HPU_EnvKeys.NUM_SHARD.value: 8,
            LLMs_VLLM_HPU_EnvKeys.VLLM_TP_SIZE.value: 8,
            LLMs_VLLM_HPU_EnvKeys.SHARDED.value: "true",
            LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x22B-Instruct-v0.1",
        },
        "config_extra": {},
        "docker_extra": {},
    },
]

GENERAL_BENCHMARK_PARAMETERS = {
    "service": ["model_server"],
    "streaming": [True],
    "num_burst_requests": [1, 4, 8],
    "input_token_num": [128, 256, 512, 1024, 2048],
    "max_new_tokens": [512, 1024],
}

MODEL_RELATED_TOKEN_NUMS = [
    context_size_mul(0.5),
]


def test_pytest_stream():
    parameters_combinations = generate_combinations(GENERAL_BENCHMARK_PARAMETERS)

    benchmark = VllmHpuBenchmark(
        HARDCODED_SETUP_CONFIGURATIONS,
        parameters_combinations,
        MODEL_RELATED_TOKEN_NUMS,
    )

    benchmark.run()
    benchmark.save_results_as_csv("benchmark_results_stream.csv")
