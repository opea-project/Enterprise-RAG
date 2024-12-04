
"""
Tests defined here are abstract and requires child classes
with a concrete fixture to inject on runtime.
"""

import logging
from http import HTTPStatus

import allure
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BaseLLMsTest:
    """This tests use fixture that are defined in cpu and hpu concretizations."""
    def test_simple_scenario(self, llms_containers_fixture, allure_ids):
        """Verify HTTP response 200."""
        containers, configuration_id = llms_containers_fixture
        try:
            allure_id = allure_ids[(BaseLLMsTest.test_simple_scenario, configuration_id)]
            allure.dynamic.link(allure_id)
        except KeyError:
            logger.error("This test has no Zephyr binding!")

        url = (
            f"http://{containers._HOST_IP}:{containers.MICROSERVICE_API_PORT}/v1/chat/completions"
        )
        request_body = {
            "query": "What is Deep Learning?",
            "max_new_tokens": 17,
            "top_k": 10,
            "top_p": 0.95,
            "typical_p": 0.95,
            "temperature": 0.01,
            "repetition_penalty": 1.03,
            "streaming": False
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=request_body, headers=headers)

        assert response.status_code == HTTPStatus.OK, "Incorrect response status code"
