# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import yaml
from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader
import re

class LoadYaml(AbstractLoader):
    def extract_text(self):
        """Load and extract text from yaml file."""
        content = None
        try:
            with open(self.file_path, 'r') as f:
                data = yaml.safe_load(f)
                content = yaml.dump(data)
        except yaml.YAMLError:
            with open(self.file_path, 'r') as f:
                content = f.read()
                jinja_pattern = re.compile(r'{{.*?}}|{%.*?%}')
                if not jinja_pattern.search(content):
                    raise ValueError(f"File {self.file_path} is not a valid yaml file.")

        return content
