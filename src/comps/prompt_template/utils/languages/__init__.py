# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Importing language modules triggers PromptLanguage auto-registration
# via __init_subclass__.  To add a new language, import its module here.
from comps.prompt_template.utils.languages.english import EnglishLanguage  # noqa: F401
from comps.prompt_template.utils.languages.polish import PolishLanguage    # noqa: F401
