#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import allure
import pytest

import eval_multihop

logger = logging.getLogger(__name__)


def main_run(args_mock):
    with patch('sys.argv', ['script_name']):
        real_args = eval_multihop.args_parser()

    for key, value in vars(args_mock).items():
        setattr(real_args, key, value)

    with patch('eval_multihop.argparse.ArgumentParser') as mock_parser:
        mock_parser = mock_parser.return_value
        mock_parser.parse_args.return_value = real_args
        eval_multihop.main()


def test_ingest_docs():
    args = MagicMock(ingest_docs=True)
    main_run(args)


@pytest.mark.usefixtures("allure_attach_output")
def test_generation_metrics():
    args = MagicMock(generation_metrics=True)
    main_run(args)


@pytest.mark.usefixtures("allure_attach_output")
def test_retrieval_metrics():
    args = MagicMock(retrieval_metrics=True)
    main_run(args)


def test_ragas_metrics():
    args = MagicMock(ragas_metrics=True)
    main_run(args)


@pytest.fixture
def allure_attach_output():
    yield
    logger.info("allure_attach_output fixture called")
    target_dir = Path("./output/")
    if not target_dir.exists():
        logger.warning("./output dir not exists")
        return

    for file_path in target_dir.iterdir():
        logger.info(f"attaching file to allure: {file_path}")
        if file_path.is_file():
            allure.attach.file(str(file_path), name=file_path.name)
