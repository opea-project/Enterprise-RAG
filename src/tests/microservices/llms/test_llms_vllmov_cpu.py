import logging
from enum import Enum

import pytest
from src.tests.microservices.llms.base_tests import BaseLLMsTest
from src.tests.docker_setups.llms.vllm_ov_cpu import LLMsVllmOV_CPU_DockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestConfigurationLabels(Enum):
    GOLDEN = "golden"

# Test id in Jira depends on test itself and configuration
ALLURE_IDS = {
    (BaseLLMsTest.test_simple_scenario,     TestConfigurationLabels.GOLDEN): "IEASG-T97",
}

TEST_ITERATAIONS = [
    {
        "metadata": {
            "configuration-id": TestConfigurationLabels.GOLDEN,
        },
        "config": {}
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
    logger.debug("Creating LLMs VLLM+OpenVino CPU fixture with following config:")
    logger.debug(config_override)

    containers = LLMsVllmOV_CPU_DockerSetup("comps/llms/impl/model_server/vllm/docker/.env.cpu", config_override)

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
@pytest.mark.vllm
class Test_LLMs_VllmOV_CPU(BaseLLMsTest):
    pass
