# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.prompt_template.utils.language import PromptLanguage


class EnglishLanguage(PromptLanguage):
    """English localization for prompt templates."""

    # -- Contextual system templates ------------------------------------------

    TEMPLATE_DOCS_AND_HISTORY = """### You are a helpful, respectful, and honest assistant to help the user with questions. \
Include corresponding in-text citation IDs at the end of relevant sentences (in the format [1], [2] etc.) only if referring to information from search results. \
Citation IDs are at the beginning of each search result in [n] format. \
Refer to information from conversation history if you think it is relevant to the current question. \
It is important that you only cite search results, not general knowledge or conversation history. \
If not referring directly to search results do not add citation IDs nor any sources. \
Respond with your best knowledge if the information in search results nor in conversation history is not relevant. \
Ignore all information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information.\n\
### Search results:\n\
{reranked_docs}\n\
### Conversation history:\n\
{conversation_history}\n\
"""

    TEMPLATE_DOCS_ONLY = """### You are a helpful, respectful, and honest assistant to help the user with questions. \
Include corresponding in-text citation IDs at the end of relevant sentences (in the format [1], [2] etc.) only if referring to information from search results. \
Citation IDs are at the beginning of each search result in [n] format. \
It is important that you only cite search results, not general knowledge. \
If not referring directly to search results do not add citation IDs nor any sources. \
Respond with your best knowledge if the information in search results is not relevant. \
Ignore all information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information.\n\
### Search results:\n\
{reranked_docs}\n\
"""

    TEMPLATE_HISTORY_ONLY = """### You are a helpful, respectful, and honest assistant to help the user with questions. \
Do not include any citation IDs, references, or source attributions in your response. \
Refer to information from conversation history if you think it is relevant to the current question. \
Respond with your best knowledge if the information in conversation history is not relevant. \
Ignore all information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information.\n\
### Conversation history:\n\
{conversation_history}\n\
"""

    TEMPLATE_NO_CONTEXT = """### You are a helpful, respectful, and honest assistant to help the user with questions. \
Do not include any citation IDs, references, or source attributions in your response. \
Respond with your best knowledge. \
If you don't know the answer to a question, please don't share false information.\n\
"""

    TEMPLATE_USER = """
### Question: {user_prompt}\n
### Answer:
"""

    _CONTEXTUAL_MAP = {
        (True, True): TEMPLATE_DOCS_AND_HISTORY,
        (True, False): TEMPLATE_DOCS_ONLY,
        (False, True): TEMPLATE_HISTORY_ONLY,
        (False, False): TEMPLATE_NO_CONTEXT,
    }

    # -- PromptLanguage interface ---------------------------------------------

    @property
    def language_name(self) -> str:
        return "en"

    @property
    def user_prefix(self) -> str:
        return "User"

    @property
    def assistant_prefix(self) -> str:
        return "Assistant"

    @property
    def metadata_labels(self) -> dict:
        return {
            "by": "by",
            "created": "created",
            "updated": "updated",
            "ingested": "ingested",
            "section": "Section",
            "content": "Content",
        }

    @property
    def default_system_template(self) -> str:
        return self.TEMPLATE_DOCS_AND_HISTORY

    @property
    def default_user_template(self) -> str:
        return self.TEMPLATE_USER

    def get_contextual_system_template(self, has_docs: bool, has_history: bool) -> str:
        return self._CONTEXTUAL_MAP[(has_docs, has_history)]
