import logging

import pytest
from llms.base_tests import BaseLLMsTest
from llms.structures_llms_vllm import (LLMs_VLLM_EnvKeys,
                                       LLMsVllmDockerSetup)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TEST_ITERATAIONS = [
    {
        "metadata": {
            "test-id": "golden",
            "allure-id": "IEASG-T60",
        },
        "config": {}
    },
    {
        "metadata": {
            "test-id": "Mixtral-8x22B-Instruct-v0.1",
            "allure-id": "IEASG-T70",
        },
        "config": {
            LLMs_VLLM_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x22B-Instruct-v0.1"
        }
    },
    {
        "metadata": {
            "test-id": "Meta-Llama-3-70B",
            "allure-id": "IEASG-T71",
        },
        "config": {
            LLMs_VLLM_EnvKeys.LLM_VLLM_MODEL_NAME.value: "meta-llama/Meta-Llama-3-70B"
        }
    },
]

@pytest.fixture(
    params=TEST_ITERATAIONS,
    ids=[i["metadata"]["test-id"] for i in TEST_ITERATAIONS],
    scope="module",
    autouse=True
)
def llms_containers_fixture(request):
    config_override = request.param["config"]
    logger.debug("Creating LLMs VLLM HPU fixture with following config:")
    logger.debug(config_override)

    containers = LLMsVllmDockerSetup("comps/llms/impl/model_server/vllm/docker/.env.hpu", config_override)

    try:
        containers.deploy()
        containers_annotated = (
            containers,
            request.param["metadata"]["allure-id"],
        )
        yield containers_annotated
    finally:
        containers.destroy()

@pytest.mark.llms
@pytest.mark.hpu
@pytest.mark.vllm
class Test_LLMs_VLLM_HPU(BaseLLMsTest):
    pass
