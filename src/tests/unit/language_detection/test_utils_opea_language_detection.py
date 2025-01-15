# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest

from comps.language_detection.utils.opea_language_detection import OPEALanguageDetector
from comps import (
    GeneratedDoc,
    LLMParamsDoc,
)


@pytest.fixture
def test_class():
    """Fixture to create OPEATranslator instance."""
    return OPEALanguageDetector()

@pytest.fixture
def mock_input_data():
    """Fixture to provide mock input data."""
    return GeneratedDoc(
        text="Hi. I am doing fine.",
        prompt= """
### You are a helpful, respectful, and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results:   \n
### Question: 你好。你好吗？ \n
### Answer:
""".strip()
    )


def test_initialization_succeeds():
    # Assert that the instance is created successfully
    assert isinstance(OPEALanguageDetector(), OPEALanguageDetector), "Instance was not created successfully."

def test_run_succeeds(test_class, mock_input_data):
    # Assert that the method returns an LLMParamsDoc object
    result = test_class.run(mock_input_data)
    assert isinstance(result, LLMParamsDoc), "Method did not return LLMParamsDoc object"

    # Assert that the constructed query is correct
    assert result.query == """
            Translate this from English to Chinese:
            English:
            Hi. I am doing fine.

            Chinese:            
        """, "LLM query returned is incorrect"
    
def test_run_raises_exception_on_empty_query(test_class):
    input_data = GeneratedDoc(text="sample answer", prompt="")

    with pytest.raises(ValueError) as context:
        test_class.run(input_data)
    
    assert str(context.value) == "Initial query cannot be empty."

def test_run_raises_exception_on_empty_answer(test_class):
    input_data = GeneratedDoc(text="", prompt="sample query")

    with pytest.raises(ValueError) as context:
        test_class.run(input_data)
    
    assert str(context.value) == "Answer from LLM cannot be empty."

def test_run_raises_exception_on_missing_question(test_class):
    input_data = GeneratedDoc(text="sample answer", prompt="sample query")

    with pytest.raises(ValueError) as context:
        test_class.run(input_data)
    
    assert str(context.value) == "Question not found in the prompt!"
