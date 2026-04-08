# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.prompt_template.utils.language import PromptLanguage


class PolishLanguage(PromptLanguage):
    """Polish localization for prompt templates."""

    # -- Contextual system templates ------------------------------------------

    TEMPLATE_DOCS_AND_HISTORY = """### Jesteś pomocnym, uprzejmym i uczciwym asystentem, \
który pomaga użytkownikowi w odpowiadaniu na zadane przez użytkownika pytania. \
Odwołuj się do informacji z historii rozmowy, jeśli uznasz, że są one istotne dla bieżącego pytania. \
Odpowiadaj na podstawie swojej najlepszej wiedzy, jeśli informacje z wyników wyszukiwania ani z historii \
rozmowy nie są istotne. Ignoruj wszystkie informacje, które uznasz za nieistotne dla pytania. \
Jeśli nie znasz odpowiedzi na pytanie, nie podawaj fałszywych informacji.\n\
### Wyniki wyszukiwania:\n\
{reranked_docs}\n\
### Historia rozmowy:\n\
{conversation_history}\n\
"""

    TEMPLATE_DOCS_ONLY = """### Jesteś pomocnym, uprzejmym i uczciwym asystentem, \
który pomaga użytkownikowi w odpowiadaniu na zadane przez użytkownika pytania. \
Odpowiadaj na podstawie swojej najlepszej wiedzy, jeśli informacje z wyników wyszukiwania nie są istotne. \
Ignoruj wszystkie informacje, które uznasz za nieistotne dla pytania. \
Jeśli nie znasz odpowiedzi na pytanie, nie podawaj fałszywych informacji.\n\
### Wyniki wyszukiwania:\n\
{reranked_docs}\n\
"""

    TEMPLATE_HISTORY_ONLY = """### Jesteś pomocnym, uprzejmym i uczciwym asystentem, \
który pomaga użytkownikowi w odpowiadaniu na zadane przez użytkownika pytania. \
Odwołuj się do informacji z historii rozmowy, jeśli uznasz, że są one istotne dla bieżącego pytania. \
Odpowiadaj na podstawie swojej najlepszej wiedzy, jeśli informacje z historii rozmowy nie są istotne. \
Ignoruj wszystkie informacje, które uznasz za nieistotne dla pytania. \
Jeśli nie znasz odpowiedzi na pytanie, nie podawaj fałszywych informacji.\n\
### Historia rozmowy:\n\
{conversation_history}\n\
"""

    TEMPLATE_NO_CONTEXT = """### Jesteś pomocnym, uprzejmym i uczciwym asystentem, \
który pomaga użytkownikowi w odpowiadaniu na zadane przez użytkownika pytania. \
Odpowiadaj na podstawie swojej najlepszej wiedzy. \
Jeśli nie znasz odpowiedzi na pytanie, nie podawaj fałszywych informacji.\n\
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
        return "pl"

    @property
    def user_prefix(self) -> str:
        return "Użytkownik"

    @property
    def assistant_prefix(self) -> str:
        return "Asystent"

    @property
    def metadata_labels(self) -> dict:
        return {
            "by": "autorstwa",
            "created": "utworzono",
            "updated": "zaktualizowano",
            "ingested": "wczytano",
            "section": "Sekcja",
            "content": "Treść",
        }

    @property
    def default_system_template(self) -> str:
        return self.TEMPLATE_DOCS_AND_HISTORY

    @property
    def default_user_template(self) -> str:
        return self.TEMPLATE_USER

    def get_contextual_system_template(self, has_docs: bool, has_history: bool) -> str:
        return self._CONTEXTUAL_MAP[(has_docs, has_history)]
