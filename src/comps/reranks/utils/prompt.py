# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import re


def get_prompt(question: str, context_str: str = "empty context") -> str:
    # Check if the context is primarily Chinese
    if (
        context_str
        and len(re.findall("[\u4e00-\u9fff]", context_str)) / len(context_str) >= 0.3
    ):
        # Chinese context
        template = """
### 你将扮演一个乐于助人、尊重他人并诚实的助手，你的目标是帮助用户解答问题。有效地利用来自本地知识库的搜索结果。确保你的回答中只包含相关信息。如果你不确定问题的答案，请避免分享不准确的信息。
### 搜索结果：{context}
### 问题：{question}
### 回答：
"""
    else:
        # English context
        template = """
### You are a helpful, respectful, and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results: {context} \n
### Question: {question} \n
### Answer:
"""
    return template.format(context=context_str, question=question).strip()


# Usage example
if __name__ == "__main__":
    print("1. Show example in Chinese:")
    context = "这里是一些示例搜索结果。"
    question = "你能帮我解答这个问题吗？"
    prompt = get_prompt(question, context)
    print(prompt)
    print("2. Show example in English:")
    context = "Here are some example search results."
    question = "Can you help me answer this question?"
    prompt = get_prompt(question, context)
    print(prompt)
