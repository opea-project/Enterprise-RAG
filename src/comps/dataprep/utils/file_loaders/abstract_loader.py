# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod


class AbstractLoader(ABC):
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_type = file_path.split('.')[-1]

    @abstractmethod
    def extract_text(self):
        raise NotImplementedError
