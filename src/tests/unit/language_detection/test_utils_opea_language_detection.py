# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest

from comps.language_detection.utils.opea_language_detection import OPEALanguageDetector
from comps import (
    GeneratedDoc,
    PromptTemplateInput,
    TranslationInput,
)


@pytest.fixture
def test_class():
    """Fixture to create OPEATranslator instance."""
    return OPEALanguageDetector()

@pytest.fixture
def test_class_standalone():
    """Fixture to create OPEATranslator instance for standalone functionality"""
    return OPEALanguageDetector(is_standalone=True)

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

@pytest.fixture
def mock_input_data_standalone():
    """Fixture to provide mock input data for standalone functionality"""
    return TranslationInput(
        text="Hi. I am doing fine.",
        target_language="German",
    )

def test_initialization_succeeds():
    # Assert that the instance is created successfully
    assert isinstance(OPEALanguageDetector(), OPEALanguageDetector), "Instance was not created successfully."
    assert isinstance(OPEALanguageDetector(is_standalone=True), OPEALanguageDetector), "Instance was not created successfully."

def test_run_succeeds(test_class, mock_input_data):
    # Assert that the method returns an PromptTemplateInput object
    result = test_class.run(mock_input_data)
    assert isinstance(result, PromptTemplateInput), "Method did not return PromptTemplateInput object"

    # Assert that the constructed query is correct
    assert result.prompt_template == """
            Translate this from {source_lang} to {target_lang}:
            {source_lang}:
            {text}

            {target_lang}:            
        """
    
    assert result.data["text"] == "Hi. I am doing fine."
    assert result.data["source_lang"] == "English"
    assert result.data["target_lang"] == "Chinese"

def test_run_suceeds_standalone(test_class_standalone, mock_input_data_standalone):
    # Assert that the method returns an PromptTemplateInput object
    result = test_class_standalone.run(mock_input_data_standalone)
    assert isinstance(result, PromptTemplateInput), "Method did not return PromptTemplateInput object"

    # Assert that the constructed query is correct
    assert result.prompt_template == """
            Translate this from {source_lang} to {target_lang}:
            {source_lang}:
            {text}

            {target_lang}:            
        """
    
    assert result.data["text"] == "Hi. I am doing fine."
    assert result.data["source_lang"] == "English"
    assert result.data["target_lang"] == "German"
    
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

def test_run_raises_exception_on_unsupported_query_language(test_class):
    input_data = GeneratedDoc(text="sample answer", prompt="""
### You are a helpful, respectful, and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results:   \n
### Question: よぷさんの調子はどうですか？ \n
### Answer:
""")

    with pytest.raises(ValueError) as context:
        test_class.run(input_data)
    
    assert str(context.value) == "Language of query is not supported."

def test_run_raises_exception_on_unsupported_answer_language(test_class):
    input_data = GeneratedDoc(text="私は元気です。", prompt="""
### You are a helpful, respectful, and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results:   \n
### Question: 你好。你好吗？ \n
### Answer:
""")

    with pytest.raises(ValueError) as context:
        test_class.run(input_data)
    
    assert str(context.value) == "Language of answer is not supported."

def test_run_standalone_raises_exception_on_empty_text(test_class_standalone):
    input_data = TranslationInput(text="", target_language="German")

    with pytest.raises(ValueError) as context:
        test_class_standalone.run(input_data)
    
    assert str(context.value) == "Text to to be translated cannot be empty."

def test_run_standalone_raises_exception_on_empty_target_lang(test_class_standalone):
    input_data = TranslationInput(text="sample text", target_language="")

    with pytest.raises(ValueError) as context:
        test_class_standalone.run(input_data)
    
    assert str(context.value) == "Target language cannot be empty."

def test_run_standalone_raises_exception_on_unsupported_text_language(test_class_standalone):
    input_data = TranslationInput(text="私は元気です", target_language="English")

    with pytest.raises(ValueError) as context:
        test_class_standalone.run(input_data)
    
    assert str(context.value) == "Original language of text is not supported."

def test_run_standalone_raises_exception_on_unsupported_target_language(test_class_standalone):
    input_data = TranslationInput(text="I am doing fine.", target_language="Japanese")

    with pytest.raises(ValueError) as context:
        test_class_standalone.run(input_data)
    
    assert str(context.value) == "Provided target language is not supported."