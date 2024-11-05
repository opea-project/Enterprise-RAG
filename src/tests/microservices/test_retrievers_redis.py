#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest

ORIGINAL_TEST = "test_retrievers_redis.sh"


@allure.testcase("IEASG-T13")
@pytest.mark.retrievers
def test_retrievers_redis(assert_bash_test_succeeds):
    assert_bash_test_succeeds(ORIGINAL_TEST)
