# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import evaluate
import jieba


def catch_all_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            print(repr(e))

    return wrapper


tokenizer = lambda text: list(jieba.cut(text)) # noqa: E731


@catch_all_exceptions
def bleu_score(continuation: str, reference: str, with_penalty=False) -> float:
    bleu = evaluate.load(os.path.join(os.path.dirname(__file__), "bleu"))
    results = bleu.compute(predictions=[continuation], references=[[reference]], tokenizer=tokenizer)

    bleu_avg = results["bleu"]
    bleu1 = results["precisions"][0]
    bleu2 = results["precisions"][1]
    bleu3 = results["precisions"][2]
    bleu4 = results["precisions"][3]
    brevity_penalty = results["brevity_penalty"]

    if with_penalty:
        return bleu_avg, bleu1, bleu2, bleu3, bleu4
    else:
        return 0.0 if brevity_penalty == 0 else bleu_avg / brevity_penalty, bleu1, bleu2, bleu3, bleu4


@catch_all_exceptions
def rougeL_score(continuation: str, reference: str) -> float:
    rouge = evaluate.load(os.path.join(os.path.dirname(__file__), "rouge"))
    results = rouge.compute(
        predictions=[continuation], references=[[reference]], tokenizer=tokenizer, rouge_types=["rougeL"]
    )
    score = results["rougeL"]
    return score
