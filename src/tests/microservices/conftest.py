#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path
from subprocess import run # nosec B404


@pytest.fixture
def assert_bash_test_succeeds():
    def _run_bash_test(test_file):
        bash_test = Path.cwd().joinpath(test_file)
        result = run(['bash', bash_test], capture_output=True, text=True)
        print(f"Stdout from bash test: {result.stdout}")
        assert result.returncode == 0, f"{test_file} failed. Captured stderr: {result.stderr}"

    return _run_bash_test
