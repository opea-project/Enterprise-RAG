import asyncio
import logging
from abc import abstractmethod
from typing import Type

from transformers import AutoConfig

from src.tests.benchmark_microservices.common.structures import (
    BenchmarkBase,
    BenchmarkParams,
    StreamRequestTimings,
    generate_combinations,
)
from src.tests.benchmark_microservices.common.targets import (
    LlmMicroserviceBenchTarget,
    VllmBenchTarget,
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
                    custom_microservice_envs=setup["config_microservice_extra"],
                    custom_model_server_envs=setup["config_model_server_extra"],
                    custom_model_server_docker_params=setup[
                        "docker_model_server_extra"
                    ],
                )
                dockers.deploy()

                model_name = dockers.get_docker_env(
                    LLMs_VLLM_HPU_EnvKeys.LLM_VLLM_MODEL_NAME
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

            except RuntimeError:
                logger.error("Docker setup failed! Continue with next setup...")
                continue

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
    "stream": [True],
    "num_burst_requests": [1, 4, 8],
    "input_token_num": [128, 256, 512, 1024, 2048],
    "max_new_tokens": [512, 1024],
}


def custom_setups_filter(input_setups: list[dict]) -> list[dict]:
    """Filters setups with contradictory settings.

    Enforced rules are:
    - NUM_SHARD == VLLM_TP_SIZE
    - len(HABANA_VISIBLE_DEVICES) == NUM_SHARD
    - HABANA_VISIBLE_DEVICES == "all" --> NUM_SHARD == 8
    - HABANA_VISIBLE_DEVICES == 1 --> SHARDED == false
    - HABANA_VISIBLE_DEVICES > 1 --> SHARDED == true
    """

    valid_setups = []
    for setup in input_setups:
        config_override = setup["config_override"]
        if config_override["NUM_SHARD"] != config_override["VLLM_TP_SIZE"]:
            logger.debug("Skip following setup, because NUM_SHARD != VLLM_TP_SIZE:")
            logger.debug(setup)
            continue
        num_habana_devices = parse_habana_devices(
            config_override["HABANA_VISIBLE_DEVICES"]
        )
        if num_habana_devices != config_override["NUM_SHARD"]:
            logger.debug("Skip following setup, because #HABANA_DEVICES != NUM_SHARD:")
            logger.debug(setup)
            continue
        if (num_habana_devices == 1) and config_override["SHARDED"]:
            logger.debug(
                "Skip following setup, because sharded is set for single habana device:"
            )
            logger.debug(setup)
            continue
        if (num_habana_devices > 1) and not config_override["SHARDED"]:
            logger.debug(
                "Skip following setup, because sharded is not set for multiple habana devices:"
            )
            logger.debug(setup)
            continue

        valid_setups.append(setup)

    logger.info(
        f"Filtered out {len(input_setups) - len(valid_setups)}, leaving {len(valid_setups)} valid ones."
    )
    return valid_setups


def parse_habana_devices(value: str) -> int:
    if value == "all":
        return 8
    devices = value.split(",")
    return len(devices)


def test_vllm_hpu():
    yaml_conf = VllmHpuBenchmark.parse_yaml_config(
        "src/tests/benchmark/config_defaults/vllm_hpu.yaml"
    )

    setup_combinations = generate_combinations(yaml_conf["setup_configurations"])
    setup_combinations = custom_setups_filter(setup_combinations)
    parameters_combinations = generate_combinations(yaml_conf["benchmark_parameters"])
    model_related_token_nums = yaml_conf["model_related_token_nums"]

    benchmark = VllmHpuBenchmark(
        setup_combinations, parameters_combinations, model_related_token_nums
    )

    benchmark.run()
    benchmark.save_results_as_csv("benchmark_results.csv")
