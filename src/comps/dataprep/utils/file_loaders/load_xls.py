# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pandas
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader


class LoadXls(AbstractLoader):
    def extract_text(self):
        """Load and process xlsx file."""
        df = pandas.read_excel(self.file_path)
        return df.to_string()
