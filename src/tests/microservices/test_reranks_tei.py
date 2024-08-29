#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#
import allure
from subprocess import run # nosec B404

from pathlib import Path

OUTPUT_DIR = "results"
ORIGINAL_TEST = "test_reranks_tei.sh"


@allure.link("https://jira.devtools.intel.com/secure/Tests.jspa#/testCase/IEASG-T5")
def test_reranks_tei():
    bash_test = Path.cwd().joinpath(ORIGINAL_TEST)
    result = run(['bash', bash_test], capture_output=True, text=True)
    print(f"Stdout from bash test: {result.stdout}")
    assert result.returncode == 0, f"{ORIGINAL_TEST} failed. Captured stderr: {result.stderr}"
