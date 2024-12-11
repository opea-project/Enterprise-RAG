# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

from comps.language_detection.utils import detector

class TestOPEATranslationLanguageDetection(unittest.TestCase):
    def test_language_detection(self):
        input_txt = "你好。我做得很好。"
        expected_output = 'zh'

        result = detector.detect_language(input_txt)
        self.assertEqual(result, expected_output)


if __name__ == "__main__":
    unittest.main()