#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
import os
from typing import Dict, Optional, Union

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_huggingface import HuggingFaceEndpoint
from langchain_openai import ChatOpenAI

# import * is only allowed at module level according to python syntax
try:
    # from ragas.metrics import *
    from ragas import evaluate
    from ragas.metrics import (
        answer_correctness,
        answer_relevancy,
        answer_similarity,
        context_precision,
        context_recall,
        faithfulness,
    )
except ModuleNotFoundError:
    raise ModuleNotFoundError("Please install ragas to use this metric. `pip install ragas`.")

try:
    from datasets import Dataset
except ModuleNotFoundError:
    raise ModuleNotFoundError("Please install dataset")

VALIDATED_LIST = [
    "answer_correctness",
    "answer_relevancy",
    "answer_similarity",
    "context_precision",
    "context_recall",
    "faithfulness",
]

metrics_mapping = {
    "answer_correctness": answer_correctness,
    "answer_relevancy": answer_relevancy,
    "answer_similarity": answer_similarity,
    "context_precision": context_precision,
    "context_recall": context_recall,
    "faithfulness": faithfulness,
}


def format_ragas_metric_name(name: str):
    return f"{name} (ragas)"


class RagasMetric:
    """This metric checks if the output is more than 3 letters."""

    def __init__(
        self,
        threshold: float = 0.3,
        model: Optional[Union[str, BaseLanguageModel]] = None,
        model_name: Optional[str] = None,
        embeddings: Optional[Embeddings] = None,
        metrics: Optional[list[str]] = None,
        use_vllm: Optional[bool] = False,
    ):
        self.threshold = threshold
        self.model = model
        self.model_name = model_name
        self.embeddings = embeddings
        self.metrics = metrics

        openai_key = os.getenv("OPENAI_API_KEY", None)
        if openai_key is not None:
            print("OPENAI_API_KEY is provided, ragas initializes the model by OpenAI.")
            self.chat_model = None
        elif isinstance(self.model, str):
            print("LLM endpoint: ", self.model)

            if use_vllm:
                openai_endpoint = f"{self.model}/v1"
                self.chat_model = ChatOpenAI(
                    openai_api_key="EMPTY",
                    openai_api_base=openai_endpoint,
                    model_name=self.model_name,
                    timeout=600,
                    max_retries=3
                )
            else:
                self.chat_model = HuggingFaceEndpoint(
                    endpoint_url=self.model,
                    timeout=600
                )

        else:
            print("Accepting user-initialized model as we could not detect OpenAI key or HuggingFace Endpoint URL.")
            self.chat_model = self.model

        if self.metrics is not None:
            tmp_metrics = []
            # check supported list
            for metric in self.metrics:
                if metric not in VALIDATED_LIST:
                    raise ValueError(
                        "metric should be in supported list {}. ".format(VALIDATED_LIST)
                        + "ClientResponseError raised with LangchainLLM "
                        + "when context_precision, context_recall ran. "
                        + "Here are the related issues described in ragas "
                        "https://github.com/explodinggradients/ragas/issues/934, "
                        + "https://github.com/explodinggradients/ragas/issues/664."
                    )
                else:
                    if metric == "answer_relevancy" and self.embeddings is None:
                        raise ValueError("AnswerRelevancy metric need provide embeddings model.")
                    tmp_metrics.append(metrics_mapping[metric])
            self.metrics = tmp_metrics
        else:
            self.metrics = [metrics_mapping[metric] for metric in VALIDATED_LIST]

        # Find necessary input fields using the given metrics
        _required_columns = set()
        column_map = {  # this column maps new naming style in ragas to their old naming style
            "user_input": "question",
            "response": "answer",
            "reference": "ground_truth",
            "retrieved_contexts": "contexts",
            "reference_contexts": "reference_contexts",
        }
        for metric in self.metrics:
            if hasattr(metric, "_required_columns"):
                for column in list(metric._required_columns.values())[0]:
                    _required_columns.add(column_map[column])
            elif hasattr(metric, "evaluation_mode"):
                from ragas.metrics.base import get_required_columns

                for column in get_required_columns(metric.evaluation_mode):
                    _required_columns.add(column)
            else:
                print("metric has no attribute denoting required columns")

        print("Required columns for given list of metrics are = {}".format(_required_columns))
        self._required_columns = _required_columns

    async def a_measure(self, test_case: Dict):
        return self.measure(test_case)

    def measure(self, test_case: Dict):
        # get only necessary columns from test case
        data = {column: test_case[column] for column in self._required_columns}
        dataset = Dataset.from_dict(data)

        # evaluate
        self.score = evaluate(
            dataset,
            metrics=self.metrics,
            llm=self.chat_model,
            embeddings=self.embeddings,
        )
        return self.score

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return "RAGAS"
