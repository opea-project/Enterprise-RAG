# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

from comps.language_detection.utils import prompt

class TestOPEATranslationPrompt(unittest.TestCase):
    def test_get_prompt_template(self):
        expected_output = """
            Translate this from {source_lang} to {target_lang}:
            {source_lang}:
            {text}

            {target_lang}:            
        """

        result = prompt.get_prompt_template()
        self.assertEqual(result, expected_output)

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
