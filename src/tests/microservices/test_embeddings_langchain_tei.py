#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest

ORIGINAL_TEST = "test_embeddings_langchain_tei.sh"


@allure.testcase("IEASG-T6")
@pytest.mark.embeddings
def test_embeddings_langchain_tei(assert_bash_test_succeeds):
    assert_bash_test_succeeds(ORIGINAL_TEST)
