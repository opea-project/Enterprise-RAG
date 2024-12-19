# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest
from docarray import DocList

from comps import (
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
            "initial_query":"This is my sample query?",
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
    return """
### You are a helpful, respectful, and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results: Document1 Document2 Document3 \n
### Question: This is my sample query? \n
### Answer:
""".strip()


def test_opea_prompt_template_initialization_succeeds():
    # Assert that the instance is created successfully
    assert isinstance(OPEAPromptTemplate(), OPEAPromptTemplate), "Instance was not created successfully."


@patch('comps.prompt_template.utils.opea_prompt_template.default_prompt_template', '')
def test_opea_prompt_template_initialization_without_default_should_fail():
    with pytest.raises(ValueError, match="Prompt template cannot be empty"):
        OPEAPromptTemplate()

@patch('comps.prompt_template.utils.opea_prompt_template.default_prompt_template', 'invalid_template')
def test_opea_prompt_template_initializationwith_invalid_template_should_fail():

     with pytest.raises(ValueError, match="Default prompt template validation failed, err=The prompt template does not contain any placeholders"):
        OPEAPromptTemplate()


@pytest.mark.parametrize("template, placeholders", [
    ("This is a valid template with {placeholder1} and {placeholder2}.", {"placeholder1", "placeholder2"}),
    ("This is a valid template where {placeholder1} is used multiple times, including here: {placeholder1}", {'placeholder1'}),
    ])
def test_opea_prompt_template_validate_suceeds(test_class, template, placeholders):
    try:
        test_class._validate(template, placeholders)
    except ValueError:
        pytest.fail("Validation failed for a valid template")


@pytest.mark.parametrize("template, placeholders, expected_message", [
    ("This is an ivalid fixed template with empty set of placeholders", set(), "The prompt template does not contain any placeholders"),
    ("This is valid template but there is no {placeholder}", None, "The set of expected placeholders cannot be empty"),
    ("", set(), "Prompt template cannot be empty"),
    ("", {'placeholder1'}, "Prompt template cannot be empty"),
    ("This is an invalid template with only one {placeholder1} but missing the other",{'placeholder1', 'placeholder2'}, "The prompt template is missing the following required placeholders: {'placeholder2'}"),
    ("This is an invalid template contains {placeholder1} and has undefined {placeholder2}", {'placeholder1'}, "The prompt template contains unexpected placeholders: {'placeholder2'}")
])
def test_opea_prompt_template_validate_raises_exception(test_class,template, placeholders, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        test_class._validate(template, placeholders)

@pytest.mark.asyncio
async def test_opea_prompt_run_suceeds_with_defaults(test_class, mock_default_input_data, mock_default_response_data):
    try:
        result = await test_class.run(mock_default_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result is not None, "Result is None"
    assert hasattr(result, 'query'), "Result does not contain field 'query'"
    assert result.query != "", "Query is empty"
    assert result.query == mock_default_response_data, "Query does not match the expected response"


@pytest.mark.asyncio
async def test_opea_prompt_run_suceeds_with_custom_prompt_template(test_class):
    mock_input = PromptTemplateInput(
        prompt_template="This is a custom prompt template with {custom_placeholder}.",
        data={
            "custom_placeholder":"the custom value",
        },
    )

    mock_response = "This is a custom prompt template with the custom value."
                                          
    try:
        result = await test_class.run(mock_input)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result is not None, "Result is None"
    assert hasattr(result, 'query'), "Result does not contain field 'query'"
    assert result.query != "", "Query is empty"
    assert result.query == mock_response, "Query does not match the expected response"


@pytest.mark.asyncio
async def test_opea_prompt_run_suceeds_with_dict_in_data(test_class):
    mock_input = PromptTemplateInput(
        prompt_template="This is a custom prompt template with {dict_placeholder}.",
        data={
            "dict_placeholder":
            {
                "value01": "the custom value",
                "value02": "provided in nested dict"
            },
        },
    )

    mock_response = "This is a custom prompt template with the custom value provided in nested dict."

    try:
        result = await test_class.run(mock_input)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result is not None, "Result is None"
    assert hasattr(result, 'query'), "Result does not contain field 'query'"
    assert result.query != "", "Query is empty"
    assert result.query == mock_response, "Query does not match the expected response"

@pytest.mark.asyncio
async def test_opea_prompt_run_raises_exception_when_template_lacks_placeholders(test_class):

    # invalid prompt template as it does not define any placeholder
    mock_invalid_input_data = PromptTemplateInput(prompt_template="This is invalid prompt template",
            data={
                "initial_query":"This is my sample query?",
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

    with pytest.raises(KeyError, match="Failed to get prompt from template, missing value for key 'initial_query'"):
        await test_class.run(mock_invalid_input_data)


@pytest.mark.asyncio
async def test_opea_prompt_run_succeeds_with_empty_value_in_reranked_docs(test_class):
    # empty text in reranked_docs
    mock_invalid_input_data = PromptTemplateInput(
            prompt_template="Answer the question '{initial_query}' based on the information from {reranked_docs}",
            data={
                "initial_query":"What is DL?",
                "reranked_docs": [
                    TextDoc(text=""),
                ],
            }
        )

    mock_response_data = "Answer the question 'What is DL?' based on the information from"
    try:
        result = await test_class.run(mock_invalid_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result is not None, "Result is None"
    assert hasattr(result, 'query'), "Result does not contain field 'query'"
    assert result.query != "", "Query is empty"
    assert result.query == mock_response_data, "Query does not match the expected response"

@pytest.mark.asyncio
async def test_opea_prompt_run_raises_exception_when_data_is_invalid(test_class):
    # step1
    mock_input_data = PromptTemplateInput(
        prompt_template="Answer the question '{placeholder1}'",
        data={
            "placeholder1":"What is DL?",
            }
        )
    
    mock_response_data = "Answer the question 'What is DL?'"

    try:
        result = await test_class.run(mock_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result.query == mock_response_data, "Query does not match the expected response"

    # step2: remove the placeholder1 from the data
    mock_invalid_input_data = PromptTemplateInput(
        prompt_template="Answer the question {placeholder1}",
        data={
            "unknown":"What is DL?",
            }
        )
    with pytest.raises(ValueError, match="The prompt template is missing the following required placeholders: {'unknown'}"):
        await test_class.run(mock_invalid_input_data)


@pytest.mark.asyncio
async def test_prompt_run_raises_exception_with_additional_fields_in_data_when_prompt_remains_unchanged(test_class):
    # step1
    mock_input_data = PromptTemplateInput(
        prompt_template="Answer the question '{placeholder1}' based on the information from {placeholder2}",
        data={
            "placeholder1":"What is DL?",
            "placeholder2": [ "Source1", "Source2"]
            }
        )
    
    mock_response_data = "Answer the question 'What is DL?' based on the information from Source1 Source2"

    try:
        result = await test_class.run(mock_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result.query == mock_response_data, "Query does not match the expected response"

    # step2: add additional field placeholder3 in data
    mock_invalid_input_data = PromptTemplateInput(
        prompt_template="Answer the question '{placeholder1}' based on the information from {placeholder2}",
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
        prompt_template="Answer the question '{placeholder1}' based on the information from {placeholder2}",
        data={
            "placeholder1":"What is DL?",
            "placeholder2": [ "Source1", "Source2"]
            }
        )
    
    mock_response_data = "Answer the question 'What is DL?' based on the information from Source1 Source2"

    try:
        result = await test_class.run(mock_input_data)
    except Exception as e:
        pytest.fail(f"OPEA Prompt Template Microservice init raised {type(e)} unexpectedly!")

    assert result.query == mock_response_data, "Query does not match the expected response"

    # step2: try to add placeholder3 to the template
    mock_invalid_input_data = PromptTemplateInput(
        prompt_template="Answer the question '{placeholder1}' based on the information from {placeholder2} and {placeholder3}",
        data={
            "placeholder1":"What is DL?",
            "placeholder2": [ "Source1", "Source2"],
            }
        )
    
    with pytest.raises(ValueError, match="The prompt template contains unexpected placeholders: {'placeholder3'}"):
        await test_class.run(mock_invalid_input_data)