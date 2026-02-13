# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

from comps.language_detection.utils import prompt

class TestOPEATranslationPrompt(unittest.TestCase):
    def test_get_prompt_template(self):
        expected_system_prompt_template = """
            You are a language translation assistant. Your task is to translate text from one language to another.
            You will be provided with the source language, target language, and the text to translate.
        """
        expected_user_prompt_template = """
            Translate this from {source_lang} to {target_lang}:
            {source_lang}: {text}
            {target_lang}:
        """


        result_system, result_user = prompt.get_prompt_template()
        self.assertEqual(result_system, expected_system_prompt_template)
        self.assertEqual(result_user, expected_user_prompt_template)

    def test_get_language_name(self):
        expected_output = "Chinese"
        result = prompt.get_language_name("zh")
        self.assertEqual(result, expected_output)

        # Negative test
        expected_output = ""
        result = prompt.get_language_name("hi")
        self.assertEqual(result, expected_output)

    def test_validate_language_name(self):
        result = prompt.validate_language_name("Chinese")
        self.assertTrue(result)

        # Negative test
        result = prompt.validate_language_name("Hindi")
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
