# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import yaml
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader


class LoadYaml(AbstractLoader):
    def extract_text(self):
        """Load and process yaml file."""
        data = None
        with open(self.file_path, 'r') as f:
            data = yaml.safe_load(f)
        return yaml.dump(data)
