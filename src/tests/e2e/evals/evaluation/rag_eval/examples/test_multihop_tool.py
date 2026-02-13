#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import os
import subprocess  # nosec B404 - subprocess used only for running test scripts with controlled inputs
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent / "eval_multihop.py"
SRC_DIR = Path(__file__).resolve().parents[6]

def run_eval_multihop(*args):
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{SRC_DIR}:{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)] + list(args),
        capture_output=True,
        text=True,
        env=env
    )
    return result


def test_tool_multihop_eval_help_flag():
    result = run_eval_multihop("--help")
    assert result.returncode == 0, f"--help failed with stderr: {result.stderr}"
    assert "--dataset_path" in result.stdout
    assert "--ingest_docs" in result.stdout
    assert "--generation_metrics" in result.stdout
    assert "--retrieval_metrics" in result.stdout


def test_tool_multihop_eval_ingest_docs():
    result = run_eval_multihop("--ingest_docs", "--limits", "1")
    error_indicators = [
        "ERROR",
        "Failed to connect",
        "Failed to resolve",
        "Max retries exceeded",
        "ConnectionError",
    ]
    for indicator in error_indicators:
        assert indicator not in result.stderr, (
            f"Found error indicator '{indicator}' in stderr:\n{result.stderr}"
        )
