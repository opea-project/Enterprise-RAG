import logging
from enum import Enum

import pytest
from llms.base_tests import BaseLLMsTest
from llms.structures_llms_tgi import LLMsTgiDockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestConfigurationLabels(Enum):
    GOLDEN = "golden"

ALLURE_IDS = {}

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
    logger.debug("Creating LLMs TGI HPU fixture with following config:")
    logger.debug(config_override)

    containers = LLMsTgiDockerSetup("comps/llms/impl/model_server/tgi/docker/.env.hpu", config_override)

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
@pytest.mark.tgi
class Test_LLMs_TGI_HPU(BaseLLMsTest):
    pass
