# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

templ_en = """Write a thorough summary of the following text. Cover the main topics, key points, and important details in 2-3 paragraphs:


"{text}"


SUMMARY:"""


templ_refine_en = """Your job is to produce a thorough final summary.
We have provided an existing summary up to a certain point, then we will provide more context.
Refine the existing summary with the new context, incorporating key points and important information. Keep the summary well-organized and informative.


Existing Summary:
"{existing_answer}"



New Context:
"{text}"



Refined Summary:

"""
