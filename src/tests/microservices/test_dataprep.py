#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import pytest

ORIGINAL_TEST = "test_dataprep.sh"


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T12")
@pytest.mark.dataprep
def test_dataprep(assert_bash_test_succeeds):
    assert_bash_test_succeeds(ORIGINAL_TEST)
