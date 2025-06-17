# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pandas
from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader


class LoadXls(AbstractLoader):
    def extract_text(self):
        """Load and process xlsx file."""
        df = pandas.read_excel(self.file_path)
        return df.to_string()
