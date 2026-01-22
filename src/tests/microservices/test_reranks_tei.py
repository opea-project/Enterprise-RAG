#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#
import allure
import pytest

ORIGINAL_TEST = "test_reranks_tei.sh"


@allure.testcase("IEASG-T5")
@pytest.mark.reranks
def test_reranks_tei_golden(assert_bash_test_succeeds):
    assert_bash_test_succeeds(ORIGINAL_TEST)
