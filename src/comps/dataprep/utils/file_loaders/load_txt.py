# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader


class LoadTxt(AbstractLoader):
    def extract_text(self):
        """Load and process txt file."""
        data = None
        with open(self.file_path, 'r') as f:
            data = f.read()
        return data
