#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest

ORIGINAL_TEST = "test_llms_text-generation_tgi.sh"


@allure.testcase("IEASG-T11")
@pytest.mark.llms
def test_llms_text_generation_tgi(assert_bash_test_succeeds):
    assert_bash_test_succeeds(ORIGINAL_TEST)
