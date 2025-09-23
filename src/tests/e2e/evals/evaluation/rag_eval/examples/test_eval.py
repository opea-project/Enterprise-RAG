#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import patch, MagicMock

import eval_multihop


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


def test_generation_metrics():
    args = MagicMock(generation_metrics=True)
    main_run(args)


def test_retrieval_metrics():
    args = MagicMock(retrieval_metrics=True)
    main_run(args)


def test_ragas_metrics():
    args = MagicMock(ragas_metrics=True)
    main_run(args)
