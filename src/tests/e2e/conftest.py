#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import pytest


@pytest.fixture(scope="session", autouse=True)
def supress_logging():
    """
    Disable logs that are too verbose and make the output unclear
    """
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    yield
