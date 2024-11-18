# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader


class LoadJson(AbstractLoader):
    def extract_text(self):
        """Load and process json file."""

        data = None
        with open(self.file_path, 'r') as f:
            data = f.read()

        content = []
        if self.file_type == "jsonl":
            for line in data.split('\n'):
                data = json.loads(line)
                content.append(data)
        else:
            content = json.loads(data)

        return json.dumps(content)
