# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import re

from comps import (
    LLMParamsDoc,
    LLMPromptTemplate,
    TextDoc,
    PromptTemplateInput,
    get_opea_logger
)

from comps.prompt_template.utils.templates import template_system_english as default_system_template
from comps.prompt_template.utils.templates import template_user_english as default_user_template
from comps.prompt_template.utils.chat_history_handler import ChatHistoryHandler

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

AVAILABLE_LANGUAGES = ["en", "pl"]

class OPEAPromptTemplate:
    def __init__(self, chat_history_endpoint: str = None, prompt_template_language: str = "en") -> None:
        self._if_conv_history_in_prompt = False
        self._chat_history_placeholder = "conversation_history"

        self.prompt_template_language = prompt_template_language.lower()
        if self.prompt_template_language not in AVAILABLE_LANGUAGES:
            err_msg = f"Prompt template language '{self.prompt_template_language}' is not supported. Available languages: {AVAILABLE_LANGUAGES}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        self.ch_handler = ChatHistoryHandler(chat_history_endpoint=chat_history_endpoint, prompt_template_language=self.prompt_template_language)
        try:
            self._validate(default_system_template, default_user_template)
            self.system_prompt_template = default_system_template
            self.user_prompt_template = default_user_template
        except ValueError as e:
            logger.error(f"Default prompt template validation failed, err={e}")
            raise ValueError(f"Default prompt template validation failed, err={e}")
        logger.info("Initializing OPEAPromptTemplate with default template")


    def _validate(self, system_prompt_template: str, user_prompt_template: str, placeholders: set = {"user_prompt", "reranked_docs"}) -> None:
        """
        Validates the given prompt template by checking for required and unexpected placeholders.
        Args:
            prompt_template (str): The prompt template string to be validated.
            placeholders (set, optional): A set of expected placeholders that should be present in the template.
                Defaults to {"user_prompt", "reranked_docs"}.
        Raises:
            ValueError: If the prompt template is empty.
            ValueError: If the prompt template does not contain any placeholders.
            ValueError: If the set of expected placeholders is empty.
            ValueError: If the prompt template is missing any expected placeholders.
            ValueError: If the prompt template contains unexpected placeholders.
        """

        if system_prompt_template.strip() == "" or user_prompt_template.strip == "":
            raise ValueError("Prompt template cannot be empty")

        # Find all placeholders in the format {placeholder}
        system_placeholders_in_template = set(extract_placeholders_from_template(system_prompt_template))
        user_placeholders_in_template = set(extract_placeholders_from_template(user_prompt_template))
        if not system_placeholders_in_template and not user_placeholders_in_template:
            raise ValueError("The prompt template does not contain any placeholders")

        if not placeholders:
            raise ValueError("The set of expected placeholders cannot be empty")

        if system_placeholders_in_template.intersection(user_placeholders_in_template) != set():
            duplicates = system_placeholders_in_template.intersection(user_placeholders_in_template)
            raise ValueError(f"System prompt cannot have same placeholders as user prompt. Found duplicates: {duplicates}")

        combined_placeholders = system_placeholders_in_template.union(user_placeholders_in_template)

         # Ensure the required placeholders are present in templates
        missing_placeholders = placeholders - combined_placeholders
        if missing_placeholders:
            raise ValueError(f"The prompt template is missing the following required placeholders: {missing_placeholders}")

        # Ensure no placeholders in templates are not in the provided placeholders set
        extra_placeholders = combined_placeholders - placeholders
        extra_placeholders_no_ch = extra_placeholders - set([self._chat_history_placeholder])
        if extra_placeholders_no_ch:
            raise ValueError(f"The prompt template contains unexpected placeholders: {extra_placeholders_no_ch}")

        if self._chat_history_placeholder not in extra_placeholders:
            logger.warning("A placeholder for conversation history is missing. LLM will not remember previous answers. " +
                           "Add {chat_history} placeholder if you want to add the conversation to LLM.")
            self._if_conv_history_in_prompt = False
        else:
            self._if_conv_history_in_prompt = True


    def _changed(self, new_system_prompt_template: str, new_user_prompt_template: str, placeholders: list) -> bool:
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
        if (new_system_prompt_template.strip() is None or new_system_prompt_template.strip() == "") and \
            (new_user_prompt_template.strip() is None or new_user_prompt_template.strip() == ""):
            logger.info("No changes made to the prompt template")
            return False

        if new_system_prompt_template == self.system_prompt_template and new_user_prompt_template == self.user_prompt_template:
            logger.info("No changes made to the prompt template; it is already set")
            return False

        try:
            self._validate(new_system_prompt_template, new_user_prompt_template, placeholders)
            self.system_prompt_template = new_system_prompt_template
            self.user_prompt_template = new_user_prompt_template
        except Exception as e:
            logger.error(f"Prompt template validation failed: {e}")
            raise

        return True


    def _get_prompt(self, **kwargs) -> str:
        """
        Generates a formatted system and user prompts strings by inserting the provided arguments
        into the prompt templates.

        Args:
            **kwargs: Arbitrary keyword arguments to be included in the prompts.

        Returns:
            tuple: The formatted system and user prompt strings.
        """
        system_prompt = self.system_prompt_template.format(**kwargs).strip()
        user_prompt = self.user_prompt_template.format(**kwargs).strip()

        return system_prompt, user_prompt

    def _parse_reranked_docs(self, reranked_docs: list, header_separator=" > ") -> str:
        """
        Parse reranked documents and format them to display source and section information.
        If docs do not have valid metadata or text, they are skipped with an error logged.

        Args:
            reranked_docs (list): List of document dictionaries containing metadata and text

        Returns:
            str: Output string with formatted document information including source and section headers.
        """
        formatted_docs = []

        for doc in reranked_docs:
            if isinstance(doc, dict):
                doc = TextDoc(**doc)
            else:
                if not isinstance(doc, TextDoc):
                    logger.error(f"Expected reranked_docs to be a list of TextDoc or dict objects, but got {type(doc)}. Skipping.")
                    continue

            if doc.text is None or doc.metadata is None:
                logger.error(f"Document {doc} does not contain metadata or text.")
                raise ValueError(f"Document {doc} does not contain metadata or text.")

            source_info = { "type": "unknown" }
            if "url" in doc.metadata:
                source_info = {
                    "type": "Link",
                    "source": doc.metadata["url"]
                }
            if "bucket_name" in doc.metadata and "object_name" in doc.metadata:
                source_info = {
                    "type": "File",
                    "source": "/".join([doc.metadata["bucket_name"], doc.metadata["object_name"]])
                }

            if source_info["type"] == "unknown":
                # Cannot reference this document in any way
                logger.warning(f"Document {doc} does not contain valid source information.")

            # Collect header information if available
            headers = []
            for i in range(1, 8):  # Check for Header1 through Header7
                header_key = f"Header{i}"
                if header_key in doc.metadata and doc.metadata[header_key]:
                    headers.append(doc.metadata[header_key])

            # Build the formatted string
            header_part = f"\nSection: {header_separator.join(headers)}" if len(headers) > 0 else ""

            if source_info["type"] == "unknown":
                formatted_doc = f"{header_part}{doc.text}"
            else:
                formatted_doc = f"[{doc.metadata['citation_id']}] ({source_info['source']}){header_part}\nContent: {doc.text}"
            formatted_docs.append(formatted_doc)

        return "\n\n".join(formatted_docs)

    async def run(self, input: PromptTemplateInput, access_token: str=None) -> LLMParamsDoc:
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
        if input.system_prompt_template is not None and input.user_prompt_template is not None:
            if self._changed(input.system_prompt_template, input.user_prompt_template, keys):
                logger.info("The prompt template has been updated.")
                logger.debug(f"System Prompt:\n{self.system_prompt_template}")
                logger.debug(f"User Prompt:\n{self.user_prompt_template}")
            else:
                logger.debug("The prompt template has not been updated.")
                # Ensure the input data keys match the expected placeholders
                # even if the prompt template has not changed
                expected_placeholders_system = extract_placeholders_from_template(self.system_prompt_template)
                expected_placeholders_user = extract_placeholders_from_template(self.user_prompt_template)
                expected_placeholders = expected_placeholders_system.union(expected_placeholders_user) - set([self._chat_history_placeholder])
                if keys != expected_placeholders:
                    logger.error(f"Input data keys do not match the expected placeholders: has {keys}, expected {expected_placeholders}")
                    raise ValueError(f"Input data keys do not match the expected placeholders: has {keys}, expected {expected_placeholders}")

        # Build the prompt data based on the input data by extracting text from nested dictionaries if needed
        final_system_prompt = ""
        final_user_prompt = ""
        prompt_data = {}

        for key, value in input.data.items():
            if key == "reranked_docs":
                prompt_data[key] = self._parse_reranked_docs(value)
            else:
                prompt_data[key] = extract_text_from_nested_dict(value)
            logger.debug(f"Extracted text for key {key}: {prompt_data[key]}")

        # Get conversation history
        if self._if_conv_history_in_prompt:
            params = {}
            prompt_data[self._chat_history_placeholder] = self.ch_handler.parse_chat_history(input.history_id,
                                                                                                             input.chat_history_parse_type,
                                                                                                             access_token,
                                                                                                             params)

        # Generate the final prompt
        try:
            final_system_prompt, final_user_prompt = self._get_prompt(**prompt_data)
            logger.debug(f"Final System Prompt: {final_system_prompt}")
            logger.debug(f"Final User Prompt: {final_user_prompt}")
        except KeyError as e:
            logger.error(f"Failed to get prompt from template, missing value for key {e}")
            raise KeyError(f"Failed to get prompt from template, missing value for key {e}")
        except Exception as e:
            logger.error(f"Failed to get prompt from template, err={e}")
            raise

        response = LLMParamsDoc(
            messages=[
                LLMPromptTemplate(role="system", content=final_system_prompt),
                LLMPromptTemplate(role="user", content=final_user_prompt)
                ],
            data=input.data)

        return response


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
        elif data is None:
            return ""
        elif isinstance(data, TextDoc):
            return data.text
        elif isinstance(data, list):
            return " ".join(extract_text_from_nested_dict(item) for item in data)
        elif isinstance(data, dict):
            return " ".join(extract_text_from_nested_dict(value) for value in data.values())
        else:
            logger.error(f"Cannot extract text from nested item(s), unsupported data type: {type(data)}")
            raise ValueError(f"Cannot extract text from nested item(s), unsupported data type: {type(data)}")
