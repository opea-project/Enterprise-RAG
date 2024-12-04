import logging
from enum import Enum

import pytest
from llms.base_tests import BaseLLMsTest
from llms.structures_llms_vllm import (LLMs_VLLM_EnvKeys,
                                       LLMsVllmDockerSetup)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestConfigurationLabels(Enum):
    GOLDEN = "golden"
    MIXTRAL_22B  = "Mixtral-8x22B-Instruct-v0.1"
    LLAMA_70B = "Meta-Llama-3-70B"

ALLURE_IDS = {
    (BaseLLMsTest.test_simple_scenario,     TestConfigurationLabels.GOLDEN): "IEASG-T60",
    (BaseLLMsTest.test_simple_scenario,     TestConfigurationLabels.MIXTRAL_22B): "IEASG-T70",
    (BaseLLMsTest.test_simple_scenario,     TestConfigurationLabels.LLAMA_70B): "IEASG-T71",
}

TEST_ITERATAIONS = [
    {
        "metadata": {
            "configuration-id": TestConfigurationLabels.GOLDEN,
        },
        "config": {}
    },
    {
        "metadata": {
            "configuration-id": TestConfigurationLabels.MIXTRAL_22B,
        },
        "config": {
            LLMs_VLLM_EnvKeys.LLM_VLLM_MODEL_NAME.value: "mistralai/Mixtral-8x22B-Instruct-v0.1"
        }
    },
    {
        "metadata": {
            "configuration-id": TestConfigurationLabels.LLAMA_70B,
        },
        "config": {
            LLMs_VLLM_EnvKeys.LLM_VLLM_MODEL_NAME.value: "meta-llama/Meta-Llama-3-70B"
        }
    },
]

@pytest.fixture(
    params=TEST_ITERATAIONS,
    ids=[i["metadata"]["configuration-id"].value for i in TEST_ITERATAIONS],
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
            request.param["metadata"]["configuration-id"],
        )
        yield containers_annotated
    finally:
        containers.destroy()

@pytest.fixture(
    scope="module",
    autouse=True
)
def allure_ids():
    return ALLURE_IDS

@pytest.mark.llms
@pytest.mark.hpu
@pytest.mark.vllm
class Test_LLMs_VLLM_HPU(BaseLLMsTest):
    pass
