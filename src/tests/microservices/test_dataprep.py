#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest

ORIGINAL_TEST = "scripts/test_dataprep.sh"


@allure.testcase("IEASG-T12")
@pytest.mark.dataprep
def test_dataprep_golden(assert_bash_test_succeeds):
    assert_bash_test_succeeds(ORIGINAL_TEST)
