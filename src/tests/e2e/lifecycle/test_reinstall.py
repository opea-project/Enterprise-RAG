#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging

logger = logging.getLogger(__name__)


# TODO: add allure test case id
@allure.testcase("IEASG-T")
def test_reinstall(k8s_helper):
    """ """
