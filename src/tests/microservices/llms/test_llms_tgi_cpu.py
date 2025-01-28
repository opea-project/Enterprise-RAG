import logging
from enum import Enum

import pytest
from src.tests.microservices.llms.base_tests import BaseLLMsTest
from src.tests.docker_setups.llms.tgi import LLMs_TGI_EnvKeys, LLMsTgiDockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestConfigurationLabels(Enum):
    GOLDEN = "golden"
    MISTRAL_7B  = "Mistral-7B-Instruct-v0.1"

# Test id in Jira depends on test itself and configuration
ALLURE_IDS = {
    (BaseLLMsTest.test_simple_scenario,     TestConfigurationLabels.GOLDEN): "IEASG-T11",
    (BaseLLMsTest.test_simple_scenario,     TestConfigurationLabels.MISTRAL_7B): "IEASG-T80",
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
            "configuration-id": TestConfigurationLabels.MISTRAL_7B,
        },
        "config": {
            LLMs_TGI_EnvKeys.LLM_TGI_MODEL_NAME.value: "mistralai/Mistral-7B-Instruct-v0.1"
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
    logger.debug("Creating LLMs TGI CPU fixture with following config:")
    logger.debug(config_override)

    containers = LLMsTgiDockerSetup(
        "ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu",
        "comps/llms/impl/model_server/tgi/docker/.env.cpu",
        config_override
    )

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
@pytest.mark.cpu
@pytest.mark.tgi
class Test_LLMs_TGI_CPU(BaseLLMsTest):
    pass
