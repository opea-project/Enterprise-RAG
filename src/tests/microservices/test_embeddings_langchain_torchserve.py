#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure

ORIGINAL_TEST = "test_embeddings_langchain_torchserve.sh"


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T7")
def test_embeddings_langchain_torchserve(assert_bash_test_succeeds):
    assert_bash_test_succeeds(ORIGINAL_TEST)
