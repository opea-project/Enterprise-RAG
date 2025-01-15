# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import re

from comps import (
    LLMParamsDoc,
    TextDoc,
    PromptTemplateInput,
    get_opea_logger
)


from comps.prompt_template.utils.templates import template_001_english as default_prompt_template

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class OPEAPromptTemplate:
    def __init__(self):

        try:
            self._validate(default_prompt_template)
            self.prompt_template = default_prompt_template
        except ValueError as e:
            logger.error(f"Default prompt template validation failed, err={e}")
            raise ValueError(f"Default prompt template validation failed, err={e}")
        logger.info("Initializing OPEAPromptTemplate with default template")


    def _validate(self, prompt_template: str, placeholders: set = {"initial_query", "reranked_docs"}) -> None:
        """
        Validates the given prompt template by checking for required and unexpected placeholders.
        Args:
            prompt_template (str): The prompt template string to be validated.
            placeholders (set, optional): A set of expected placeholders that should be present in the template.
                Defaults to {"initial_query", "reranked_docs"}.
        Raises:
            ValueError: If the prompt template is empty.
            ValueError: If the prompt template does not contain any placeholders.
            ValueError: If the set of expected placeholders is empty.
            ValueError: If the prompt template is missing any expected placeholders.
            ValueError: If the prompt template contains unexpected placeholders.
        """

        if prompt_template.strip() == "":
            raise ValueError("Prompt template cannot be empty")

        
        # Find all placeholders in the format {placeholder}
        placeholders_in_template = extract_placeholders_from_template(prompt_template)
        if not placeholders_in_template:
            raise ValueError("The prompt template does not contain any placeholders")

        if not placeholders:
            raise ValueError("The set of expected placeholders cannot be empty")

         # Ensure the required placeholders are present in the template
        missing_placeholders = placeholders - set(placeholders_in_template)
        if missing_placeholders:
            raise ValueError(f"The prompt template is missing the following required placeholders: {missing_placeholders}")

        # Ensure no placeholders in the template are not in the provided placeholders set
        extra_placeholders = set(placeholders_in_template) - placeholders
        if extra_placeholders:
            raise ValueError(f"The prompt template contains unexpected placeholders: {extra_placeholders}")



    def _changed(self, new_prompt_template: str, placeholders: list) -> bool:
        """
        Checks if the new prompt template is different from the current one and updates it if valid.
        Args:
            new_prompt_template (str): The new prompt template to be set.
            placeholders (list): A list of placeholders determined expected to be used in prompt template.
        Returns:
            bool: True if the prompt template was changed, False otherwise.
        Raises:
            Exception: If the new prompt template fails validation.
        """

        # These checks are redundant since the _changed method is called only when new_prompt_template is not empty, 
        # but they are retained for the sake of atomicity.
        if new_prompt_template.strip() is None or new_prompt_template.strip() == "":
            logger.info("No changes made to the prompt template")
            return False
        
        if new_prompt_template == self.prompt_template:
            logger.info("No changes made to the prompt template; it is already set")
            return False
        
        try:
            self._validate(new_prompt_template, placeholders)
            self.prompt_template = new_prompt_template
        except Exception as e:
            logger.error(f"Prompt template validation failed: {e}")
            raise

        return True


    def _get_prompt(self, **kwargs) -> str:
        """
        Generates a formatted prompt string by inserting the provided arguments
        into the prompt template.

        Args:
            **kwargs: Arbitrary keyword arguments to be included in the prompt.

        Returns:
            str: The formatted prompt string.
        """
        return self.prompt_template.format(**kwargs).strip()


    async def run(self, input: PromptTemplateInput) -> LLMParamsDoc:
        """
        Executes the prompt template generation process using the provided input.
        Args:
            input (PromptTemplateInput): The input data containing the prompt template and associated data.
        Returns:
            LLMParamsDoc: An object containing the generated prompt as a query.
        Raises:
            Exception: If there is an error in creating the prompt from the template.
        """

        # Extract keys from input.data dictionary
        keys = set(input.data.keys())
        logger.debug(f"Keys in input data: {keys}")

        # Update prompt template if a new one is provided in the input and logs the update.
        if input.prompt_template is not None:
            if self._changed(input.prompt_template, keys):
                logger.info("The prompt template has been updated.")
                logger.debug(f"A new prompt template: {self.prompt_template}")
            else:
                logger.debug("The prompt template has not been updated.")
                # Ensure the input data keys match the expected placeholders
                # even if the prompt template has not changed
                expected_placeholders = extract_placeholders_from_template(self.prompt_template)
                if keys != expected_placeholders:
                    logger.error(f"Input data keys do not match the expected placeholders: has {keys}, expected {expected_placeholders}")
                    raise ValueError(f"Input data keys do not match the expected placeholders: has {keys}, expected {expected_placeholders}")


        # Build the prompt data based on the input data by extracting text from nested dictionaries if needed
        final_prompt = ""
        prompt_data = {}

        for key, value in input.data.items():
            prompt_data[key] = extract_text_from_nested_dict(value)
            logger.debug(f"Extracted text for key {key}: {prompt_data[key]}")

        # Generate the final prompt
        try:
            final_prompt = self._get_prompt(**prompt_data).strip()
        except KeyError as e:
            logger.error(f"Failed to get prompt from template, missing value for key {e}")
            raise KeyError(f"Failed to get prompt from template, missing value for key {e}")
        except Exception as e:
            logger.error(f"Failed to get prompt from template, err={e}")
            raise

        return LLMParamsDoc(query=final_prompt)


def extract_placeholders_from_template(template: str) -> set:
    """
    Extract all placeholders from a given template string.

    Placeholders are expected to be in the format {placeholder_name}.

    Args:
        template (str): The template string containing placeholders.

    Returns:
        list[str]: A list of placeholder names found in the template.
    """
    return set(re.findall(r"\{(\w+)\}", template))


def extract_text_from_nested_dict(data: any) -> str:
        """
        Recursively extracts text from nested dictionaries and lists.

        Args:
            data (dict or list): The input data which may contain nested dictionaries or lists.

        Returns:
            str: The concatenated text extracted from the nested structure.
        """
        if isinstance(data, str):
            return data
        elif isinstance(data, TextDoc):
            return data.text
        elif isinstance(data, list):
            return " ".join(extract_text_from_nested_dict(item) for item in data)
        elif isinstance(data, dict):
            return " ".join(extract_text_from_nested_dict(value) for value in data.values())
        else:
            logger.error(f"Cannot extract text from nested item(s), unsupported data type: {type(data)}")
            raise ValueError(f"Cannot extract text from nested item(s), unsupported data type: {type(data)}")