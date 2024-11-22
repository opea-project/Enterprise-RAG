import logging

import pytest
from llms.base_tests import BaseLLMsTest
from llms.structures_llms_tgi import LLMs_TGI_EnvKeys, LLMsTgiDockerSetup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TEST_ITERATAIONS = [
    {
        "metadata": {
            "test-id": "golden",
            "allure-id": "IEASG-T11",
        },
        "config": {}
    },
    {
        "metadata": {
            "test-id": "Mistral-7B-Instruct-v0.1",
            "allure-id": "IEASG-T80",
        },
        "config": {
            LLMs_TGI_EnvKeys.LLM_TGI_MODEL_NAME.value: "mistralai/Mistral-7B-Instruct-v0.1"
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
    logger.debug("Creating LLMs TGI CPU fixture with following config:")
    logger.debug(config_override)

    containers = LLMsTgiDockerSetup("comps/llms/impl/model_server/tgi/docker/.env.cpu", config_override)

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
@pytest.mark.cpu
@pytest.mark.tgi
class Test_LLMs_TGI_CPU(BaseLLMsTest):
    pass
