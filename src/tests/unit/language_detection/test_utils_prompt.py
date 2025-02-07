# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

from comps.language_detection.utils import prompt

class TestOPEATranslationPrompt(unittest.TestCase):
    def test_set_prompt(self):
        query_lang = 'zh'
        answer_lang = 'en'
        answer = "Hi. I am doing fine."
        expected_output = """
            Translate this from English to Chinese:
            English:
            Hi. I am doing fine.

            Chinese:            
        """

        result = prompt.set_prompt(query_lang, answer_lang, answer)
        self.assertEqual(result, expected_output)


if __name__ == "__main__":
    unittest.main()
