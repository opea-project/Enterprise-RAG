#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Dict
import re

class RetrievalBaseMetric:

    def __init__(self, normalize: bool = True):
        """
        Initialize the retrieval metric calculator.

        Args:
            normalize (bool): If True, normalize text by removing 'None' separators before comparison.
                            If False, use exact text matching. Default is True.
        """
        self.normalize = normalize

    @staticmethod
    def normalize_text_for_comparison(text: str) -> str:
        """
        Normalize text for comparison by removing 'None' separators that may appear
        in extracted table data while preserving the actual content.

        Examples:
            "Document author: None None Institute" -> "Document author: Institute"
            "Value: None Test None Data" -> "Value: Test Data"
        """
        # Remove standalone 'None' words (surrounded by whitespace or at boundaries)
        # This handles cases like "None None" or " None " but preserves "None" if it's part of a larger word
        normalized = re.sub(r'\bNone\b', '', text)

        # Clean up multiple consecutive spaces that may result from None removal
        normalized = re.sub(r'\s+', ' ', normalized)

        # Strip leading/trailing whitespace
        normalized = normalized.strip()

        return normalized

    def measure(self, test_case: Dict):
        # question = test_case["input"]
        golden_docs = test_case["golden_context"]
        retrieval_docs = test_case["retrieval_context"]

        hits_at_10_flag = False
        hits_at_4_flag = False
        average_precision_sum = 0
        first_relevant_rank = None
        find_gold = []


        for rank, retrieved_item in enumerate(retrieval_docs[:11], start=1):
            # Normalize retrieved item for comparison
            if self.normalize:
                retrieved_text = self.normalize_text_for_comparison(retrieved_item)
            else:
                retrieved_text = retrieved_item

            # Check if any normalized golden doc is in the normalized retrieved item
            if any(gold_item in retrieved_text for gold_item in golden_docs):
                if rank <= 10:
                    hits_at_10_flag = True
                    if first_relevant_rank is None:
                        first_relevant_rank = rank
                    if rank <= 4:
                        hits_at_4_flag = True
                    # Compute precision at this rank for this query
                    count = 0
                    for gold_item in golden_docs:
                        if gold_item in retrieved_text and gold_item not in find_gold:
                            count = count + 1
                            find_gold.append(gold_item)
                    precision_at_rank = count / rank
                    average_precision_sum += precision_at_rank

        # Calculate metrics for this query
        hits_at_10 = int(hits_at_10_flag)
        hits_at_4 = int(hits_at_4_flag)
        map_at_10 = average_precision_sum / min(len(golden_docs), 10)
        mrr = 1 / first_relevant_rank if first_relevant_rank else 0

        return {
            "Hits@10": hits_at_10,
            "Hits@4": hits_at_4,
            "MAP@10": map_at_10,
            "MRR@10": mrr,
        }
