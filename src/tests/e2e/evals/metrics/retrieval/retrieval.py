#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Dict


class RetrievalBaseMetric:
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
            if any(gold_item in retrieved_item for gold_item in golden_docs):
                if rank <= 10:
                    hits_at_10_flag = True
                    if first_relevant_rank is None:
                        first_relevant_rank = rank
                    if rank <= 4:
                        hits_at_4_flag = True
                    # Compute precision at this rank for this query
                    count = 0
                    for gold_item in golden_docs:
                        if gold_item in retrieved_item and gold_item not in find_gold:
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
