#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest
ORIGINAL_TEST = "test_embeddings_langchain_ovms.sh"


@allure.testcase("IEASG-T9")
@pytest.mark.embeddings
def test_embeddings_langchain_ovms_golden(assert_bash_test_succeeds):
    assert_bash_test_succeeds(ORIGINAL_TEST)
