# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import subprocess  # nosec B404
import unittest

from comps.reranks.utils import prompt


class TestOPEARerankerValidateConfig(unittest.TestCase):
    def test_get_prompt_chinese(self):
        context = "深度学习是人工智能（AI）中的机器学习的一个子集，具有能够从无结构或未标记的数据中无监督学习的网络。也被称为深度神经学习或深度神经网络。"
        question = "什么是深度学习？"
        expected_output = """
### 你将扮演一个乐于助人、尊重他人并诚实的助手，你的目标是帮助用户解答问题。有效地利用来自本地知识库的搜索结果。确保你的回答中只包含相关信息。如果你不确定问题的答案，请避免分享不准确的信息。
### 搜索结果：深度学习是人工智能（AI）中的机器学习的一个子集，具有能够从无结构或未标记的数据中无监督学习的网络。也被称为深度神经学习或深度神经网络。
### 问题：什么是深度学习？
### 回答：
""".strip()
        result = prompt.get_prompt(question, context)
        self.assertEqual(result, expected_output)

    def test_get_prompt_english(self):
        context = "Deep learning is a subset of machine learning in artificial intelligence (AI) that has networks capable of learning unsupervised from data that is unstructured or unlabeled. Also known as deep neural learning or deep neural network."
        question = "What is deep learning?"
        expected_output = """
### You are a helpful, respectful, and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results: Deep learning is a subset of machine learning in artificial intelligence (AI) that has networks capable of learning unsupervised from data that is unstructured or unlabeled. Also known as deep neural learning or deep neural network. \n
### Question: What is deep learning? \n
### Answer:
""".strip()
        result = prompt.get_prompt(question, context)
        self.assertEqual(result, expected_output)
        # assert result == expected_output

    def test_main_example(self):
        try:
            subprocess.run(["python", "comps/reranks/utils/prompt.py"], check=True)  # nosec B404
        except subprocess.CalledProcessError as e:
            self.fail(f"Execution of prompt.py raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
