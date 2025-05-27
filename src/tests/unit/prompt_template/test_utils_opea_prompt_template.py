# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest
from docarray import DocList

from comps import (
    PrevQuestionDetails,
    LLMPromptTemplate,
    PromptTemplateInput,
    TextDoc,
)
from comps.prompt_template.utils.opea_prompt_template import OPEAPromptTemplate

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/prompt_template --cov-report=term --cov-report=html tests/unit/prompt_template/test_utils_opea_prompt_template.py

Alternatively, to run all tests for the 'prompt_template' module, execute the following command:
   pytest --disable-warnings --cov=comps/prompt_template --cov-report=term --cov-report=html tests/unit/prompt_template
"""

@pytest.fixture
def test_class():
    """Fixture to create OPEAPromptTemplate instance."""
    return OPEAPromptTemplate()

@pytest.fixture
def mock_default_input_data():
    """Fixture to provide mock input data."""
    return PromptTemplateInput(prompt_template=None,
        data={
            "user_prompt":"This is my sample query?",
            "reranked_docs": DocList([
                TextDoc(text="Document1"),
                TextDoc(text="Document2"),
                TextDoc(text="Document3"),
            ]),
        }
    )


@pytest.fixture
def mock_default_response_data():
    """Fixture to provide mock response data."""
    return LLMPromptTemplate(system="### You are a helpful, respectful, and honest assistant to help the user with questions. " \
        "Please refer to the search results obtained from the local knowledge base. " \
        "Refer also to the conversation history if you think it is relevant to the current question. " \
        "Ignore all information that you think is not relevant to the question. " \
        "If you don't know the answer to a question, please don't share false information. \n" \
        " ### Search results: Document1 Document2 Document3\n### Conversation history:",
                             user="### Question: This is my sample query? \n\n### Answer:")


@pytest.fixture
def mock_default_input_data_with_conversation_history():
    """Fixture to provide mock input data."""
    return PromptTemplateInput(prompt_template=None,
        data={
            "user_prompt":"This is my sample query?",
            "reranked_docs": DocList([
                TextDoc(text="Document1"),
                TextDoc(text="Document2"),
                TextDoc(text="Document3"),
            ])
        },
        conversation_history=[
            PrevQuestionDetails(question="Previous question 1", answer="Previous answer 1"),
            PrevQuestionDetails(question="Previous question 2", answer="Previous answer 2"),
            PrevQuestionDetails(question="Previous question 3", answer="Previous answer 3"),
            PrevQuestionDetails(question="Previous question 4", answer="Previous answer 4"),]
    )


@pytest.fixture
def mock_default_response_data_with_conversation_history():
    """Fixture to provide mock response data."""
    return LLMPromptTemplate(system="### You are a helpful, respectful, and honest assistant to help the user with questions. " \
        "Please refer to the search results obtained from the local knowledge base. " \
        "Refer also to the conversation history if you think it is relevant to the current question. " \
        "Ignore all information that you think is not relevant to the question. " \
        "If you don't know the answer to a question, please don't share false information. \n" \
        " ### Search results: Document1 Document2 Document3\n" \
        "### Conversation history: previous_question: Previous question 2 previous_answer: Previous answer 2 previous_question: Previous question 3 previous_answer: Previous answer 3 previous_question: Previous question 4 previous_answer: Previous answer 4",
                             user="### Question: This is my sample query? \n\n### Answer:")


def test_opea_prompt_template_initialization_succeeds():
    # Assert that the instance is created successfully
    assert isinstance(OPEAPromptTemplate(), OPEAPromptTemplate), "Instance was not created successfully."


@patch('comps.prompt_template.utils.opea_prompt_template.default_system_template', '')
@patch('comps.prompt_template.utils.opea_prompt_template.default_user_template', '')
def test_opea_prompt_template_initialization_without_default_should_fail():
    with pytest.raises(ValueError, match="Prompt template cannot be empty"):
        OPEAPromptTemplate()

@patch('comps.prompt_template.utils.opea_prompt_template.default_system_template', 'invalid_template')
@patch('comps.prompt_template.utils.opea_prompt_template.default_user_template', 'invalid_template')
def test_opea_prompt_template_initializationwith_invalid_template_should_fail():

     with pytest.raises(ValueError, match="Default prompt template validation failed, err=The prompt template does not contain any placeholders"):
        OPEAPromptTemplate()


@pytest.mark.parametrize("system_template, user_template, placeholders", [
    ("This is a valid template with {placeholder1}.", "Ths is a valid user template with {placeholder2}", {"placeholder1", "placeholder2"}),
    ("This is a valid template where {placeholder1} is used multiple times, including here: {placeholder1}", "This is user template {placeholder2}", {'placeholder1', 'placeholder2'}),
    ])
def test_opea_prompt_template_validate_suceeds(test_class, system_template, user_template, placeholders):
    try:
        test_class._validate(system_template, user_template, placeholders)
    except ValueError:
        pytest.fail("Validation failed for a valid template")


@pytest.mark.parametrize("system_template, user_template, placeholders, expected_message", [
    ("This is an ivalid fixed template with empty set of placeholders", "This is an ivalid fixed template with empty set of placeholders", set(), "The prompt template does not contain any placeholders"),
    ("This is valid template but there is no {placeholder}", "This is valid template but there is no {placeholder2}", None, "The set of expected placeholders cannot be empty"),
    ("", "", set(), "Prompt template cannot be empty"),
    ("", "", {'placeholder1'}, "Prompt template cannot be empty"),
    ("This is an invalid template with only one {placeholder1} but missing the other", "This is an invalid template contains {placeholder3}", {'placeholder1', 'placeholder2', 'placeholder3'}, "The prompt template is missing the following required placeholders: {'placeholder2'}"),
    ("This is an invalid template contains {placeholder1} and has undefined {placeholder2}", "This is an invalid template contains {placeholder3}", {'placeholder1', 'placeholder3'}, "The prompt template contains unexpected placeholders: {'placeholder2'}")
])
def test_opea_prompt_template_validate_raises_exception(test_class, system_template, user_template, placeholders, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        test_class._validate(system_template, user_template, placeholders)

@pytest.mark.asyncio
async def test_opea_prompt_run_suceeds_with_defaults(test_class, mock_default_input_data, mock_default_response_data):
    try:
        result = await test_class.run(mock_default_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result is not None, "Result is None"
    assert hasattr(result, 'messages'), "Result does not contain field 'messages'"
    assert result.messages is not None, "Messages are empty"
    assert result.messages.system == mock_default_response_data.system, "Query does not match the expected response"
    assert result.messages.user == mock_default_response_data.user, "Query does not match the expected response"


@pytest.mark.asyncio
async def test_opea_prompt_run_suceeds_with_conversation_history(test_class, mock_default_input_data_with_conversation_history, mock_default_response_data_with_conversation_history):
    try:
        result = await test_class.run(mock_default_input_data_with_conversation_history)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result is not None, "Result is None"
    assert hasattr(result, 'messages'), "Result does not contain field 'query'"
    assert result.messages is not None, "Messages are empty"
    assert result.messages.system == mock_default_response_data_with_conversation_history.system, "Query does not match the expected response"
    assert result.messages.user == mock_default_response_data_with_conversation_history.user, "Query does not match the expected response"


@pytest.mark.asyncio
async def test_opea_prompt_run_suceeds_with_custom_prompt_template(test_class):
    mock_input = PromptTemplateInput(
        system_prompt_template="This is a custom prompt template with {custom_placeholder}.",
        user_prompt_template="This is a custom user prompt template with {custom_user_placeholder}.",
        data={
            "custom_placeholder":"the custom value",
            "custom_user_placeholder":"the custom user value",
        },
    )

    mock_system_response = "This is a custom prompt template with the custom value."
    mock_user_response = "This is a custom user prompt template with the custom user value."

    try:
        result = await test_class.run(mock_input)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result is not None, "Result is None"
    assert hasattr(result, 'messages'), "Result does not contain field 'messages'"
    assert result.messages is not None, "Messages are empty"
    assert result.messages.system == mock_system_response, "Query does not match the expected response"
    assert result.messages.user == mock_user_response, "Query does not match the expected response"


@pytest.mark.asyncio
async def test_opea_prompt_run_suceeds_with_dict_in_data(test_class):
    mock_input = PromptTemplateInput(
        system_prompt_template="This is a custom prompt template with {dict_placeholder}.",
        user_prompt_template="This is custom user prompt template with {user_placeholder}.",
        data={
            "dict_placeholder":
            {
                "value01": "the custom value",
                "value02": "provided in nested dict"
            },
            "user_placeholder": "hello"
        },
    )

    mock_system_response = "This is a custom prompt template with the custom value provided in nested dict."
    mock_user_response = "This is custom user prompt template with hello."

    try:
        result = await test_class.run(mock_input)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result is not None, "Result is None"
    assert hasattr(result, 'messages'), "Result does not contain field 'messages'"
    assert result.messages is not None, "Messages are empty"
    assert result.messages.system == mock_system_response, "Query does not match the expected response"
    assert result.messages.user == mock_user_response, "Query does not match the expected response"

@pytest.mark.asyncio
async def test_opea_prompt_run_raises_exception_when_template_lacks_placeholders(test_class):

    # invalid prompt template as it does not define any placeholder
    mock_invalid_input_data = PromptTemplateInput(
            system_prompt_template="This is invalid prompt template",
            user_prompt_template="This is invalid prompt template",
            data={
                "user_prompt":"This is my sample query?",
                "reranked_docs": [
                    TextDoc(text="Document1"),
                    TextDoc(text="Document2"),
                    TextDoc(text="Document3"),
                ],
            }
        )

    with pytest.raises(ValueError, match="The prompt template does not contain any placeholders"):
        await test_class.run(mock_invalid_input_data)

@pytest.mark.asyncio
async def test_opea_prompt_run_raises_exception_when_data_key_is_missing(test_class):
    # missing initial_query
    mock_invalid_input_data = PromptTemplateInput(
            data={
                "reranked_docs": [
                    TextDoc(text="Document1"),
                    TextDoc(text="Document2"),
                    TextDoc(text="Document3"),
                ],
            }
        )

    with pytest.raises(KeyError, match="Failed to get prompt from template, missing value for key 'user_prompt'"):
        await test_class.run(mock_invalid_input_data)


@pytest.mark.asyncio
async def test_opea_prompt_run_succeeds_with_empty_value_in_reranked_docs(test_class):
    # empty text in reranked_docs
    mock_invalid_input_data = PromptTemplateInput(
            system_prompt_template="Answer the question based on the information from {reranked_docs}",
            user_prompt_template="User question: '{initial_query}'",
            data={
                "initial_query":"What is DL?",
                "reranked_docs": [
                    TextDoc(text=""),
                ],
            }
        )

    mock_system_response_data = "Answer the question based on the information from"
    mock_user_response_data = "User question: 'What is DL?'"
    try:
        result = await test_class.run(mock_invalid_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result is not None, "Result is None"
    assert hasattr(result, 'messages'), "Result does not contain field 'messages'"
    assert result.messages is not None, "Messages are empty"
    assert result.messages.system == mock_system_response_data, "Query does not match the expected response"
    assert result.messages.user == mock_user_response_data, "Query does not match the expected response"

@pytest.mark.asyncio
async def test_opea_prompt_run_raises_exception_when_data_is_invalid(test_class):
    # step1
    mock_input_data = PromptTemplateInput(
        system_prompt_template="You're a helpful assistant. Based on {placeholder1}",
        user_prompt_template="Answer the question '{placeholder2}'",
        data={
            "placeholder1": "input",
            "placeholder2": "What is DL?",
            }
        )

    mock_system_response_data = "You're a helpful assistant. Based on input"
    mock_user_response_data = "Answer the question 'What is DL?'"

    try:
        result = await test_class.run(mock_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result.messages.system == mock_system_response_data, "Query does not match the expected response"
    assert result.messages.user == mock_user_response_data, "Query does not match the expected response"

    # step2: remove the placeholder1 from the data
    mock_invalid_input_data = PromptTemplateInput(
        system_prompt_template="You're a helpful assistant. Based on {placeholder1}",
        user_prompt_template="Answer the question {placeholder2}",
        data={
            "placeholder1": "input",
            "unknown": "What is DL?",
            }
        )
    with pytest.raises(ValueError, match="The prompt template is missing the following required placeholders: {'unknown'}"):
        await test_class.run(mock_invalid_input_data)


@pytest.mark.asyncio
async def test_prompt_run_raises_exception_with_additional_fields_in_data_when_prompt_remains_unchanged(test_class):
    # step1
    mock_input_data = PromptTemplateInput(
        system_prompt_template="Based on the information from {placeholder2}",
        user_prompt_template="Answer the question '{placeholder1}'",
        data={
            "placeholder1":"What is DL?",
            "placeholder2": [ "Source1", "Source2"]
            }
        )

    mock_system_response_data = "Based on the information from Source1 Source2"
    mock_user_response_data = "Answer the question 'What is DL?'"

    try:
        result = await test_class.run(mock_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result.messages.system == mock_system_response_data, "Query does not match the expected response"
    assert result.messages.user == mock_user_response_data, "Query does not match the expected response"

    # step2: add additional field placeholder3 in data
    mock_invalid_input_data = PromptTemplateInput(
        system_prompt_template="Based on the information from {placeholder2}",
        user_prompt_template="Answer the question '{placeholder1}'",
        data={
            "placeholder1":"What is DL?",
            "placeholder2": [ "Source1", "Source2"],
            "placeholder3": "Addons",
            }
        )

    with pytest.raises(ValueError, match="Input data keys do not match the expected placeholders"):
        await test_class.run(mock_invalid_input_data)


@pytest.mark.asyncio
async def test_operator_prompt_run_raises_exception_on_unexpected_placeholder_in_template(test_class):
    # step1
    mock_input_data = PromptTemplateInput(
        system_prompt_template="Based on the information from {placeholder2}",
        user_prompt_template="Answer the question '{placeholder1}'",
        data={
            "placeholder1":"What is DL?",
            "placeholder2": [ "Source1", "Source2"]
            }
        )

    mock_system_response_data = "Based on the information from Source1 Source2"
    mock_user_response_data = "Answer the question 'What is DL?'"

    try:
        result = await test_class.run(mock_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result.messages.system == mock_system_response_data, "Query does not match the expected response"
    assert result.messages.user == mock_user_response_data, "Query does not match the expected response"

    # step2: try to add placeholder3 to the template
    mock_invalid_input_data = PromptTemplateInput(
        system_prompt_template="Based on the information from {placeholder2} and {placeholder3}",
        user_prompt_template="Answer the question '{placeholder1}'",
        data={
            "placeholder1":"What is DL?",
            "placeholder2": [ "Source1", "Source2"],
            }
        )

    with pytest.raises(ValueError, match="The prompt template contains unexpected placeholders: {'placeholder3'}"):
        await test_class.run(mock_invalid_input_data)