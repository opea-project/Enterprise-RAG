#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
import subprocess # nosec B404
from pathlib import Path


@pytest.fixture
def assert_bash_test_succeeds():
    def _run_bash_test(test_file):
        bash_test = Path.cwd().joinpath(test_file)

        # We want to see live logs from bash scripts so inside
        # bash scripts we have 'set -xe' declaration. However, this
        # prints the logs to stderr. So here we merge stdout and stderr
        # outputs into the same PIPE and log them line by line.
        p = subprocess.Popen(['bash', bash_test], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = []
        for line in iter(p.stdout.readline, b''):
            print(line)
            output.append(str(line))
        p.stdout.close()
        p.wait()

        error_msg = ""
        if p.returncode != 0:
            error_msg = "\n".join(output[-50:])

        assert p.returncode == 0, f"{test_file} failed (exit code is different than 0). Last 50 lines from output: {error_msg}"

    return _run_bash_test
