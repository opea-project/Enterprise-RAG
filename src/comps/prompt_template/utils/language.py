# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Dict, List


class PromptLanguage(ABC):
    """Abstract base class defining the localization contract for prompt templates.

    To add a new language:
    1. Create a module in ``utils/languages/`` (e.g. ``german.py``).
    2. Subclass :class:`PromptLanguage` and implement every abstract member.
    3. Import the module in ``utils/languages/__init__.py``.

    Registration happens automatically at import time via
    :meth:`__init_subclass__`.
    """

    _registry: Dict[str, "PromptLanguage"] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Only register fully concrete classes
        if not getattr(cls, "__abstractmethods__", None):
            instance = cls()
            cls._registry[instance.language_name] = instance

    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Return the list of currently registered language codes."""
        return list(cls._registry.keys())

    @classmethod
    def get(cls, language_code: str) -> "PromptLanguage":
        """Retrieve the registered :class:`PromptLanguage` for *language_code*.

        Raises :class:`ValueError` when the language is not registered.
        """
        language_code = language_code.lower()
        if language_code not in cls._registry:
            supported = cls.get_supported_languages()
            raise ValueError(
                f"Prompt template language '{language_code}' is not supported. "
                f"Available languages: {supported}"
            )
        return cls._registry[language_code]

    # -- Abstract interface ---------------------------------------------------

    @property
    @abstractmethod
    def language_name(self) -> str:
        """ISO 639-1 language code (e.g. ``'en'``, ``'pl'``)."""

    @property
    @abstractmethod
    def user_prefix(self) -> str:
        """Prefix for user turns in formatted chat history."""

    @property
    @abstractmethod
    def assistant_prefix(self) -> str:
        """Prefix for assistant turns in formatted chat history."""

    @property
    @abstractmethod
    def metadata_labels(self) -> dict:
        """Labels used when formatting reranked-document metadata.

        Must include keys: ``by``, ``created``, ``updated``, ``ingested``,
        ``section``, ``content``.
        """

    @property
    @abstractmethod
    def default_system_template(self) -> str:
        """System prompt template used by default (docs + history variant)."""

    @property
    @abstractmethod
    def default_user_template(self) -> str:
        """User prompt template."""

    @abstractmethod
    def get_contextual_system_template(self, has_docs: bool, has_history: bool) -> str:
        """Return the system template matching the given context flags."""

    # -- Shared helpers -------------------------------------------------------

    def is_default_template(self, system_template: str) -> bool:
        """Check whether *system_template* matches the default template.

        Uses whitespace-normalized comparison to tolerate minor formatting
        differences.
        """
        return system_template.split() == self.default_system_template.split()
