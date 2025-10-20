# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

templ_en = """Write a concise summary of the following:


"{text}"


CONCISE SUMMARY:"""


templ_refine_en = """Your job is to produce a final summary.
We have provided an existing summary up to a certain point, then we will provide more context.
You need to refine the existing summary (only if needed) with new context and generate a final summary.


Existing Summary:
"{existing_answer}"



New Context:
"{text}"



Final Summary:

"""
