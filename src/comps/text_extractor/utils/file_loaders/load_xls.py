# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pandas
from openpyxl import load_workbook
from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class LoadXls(AbstractLoader):
    def extract_text(self):
        """Load and process xlsx file."""
        df = pandas.read_excel(self.file_path)
        return df.to_string()

    def extract_metadata(self):
        """Extract rich metadata from XLSX document properties."""
        metadata = super().extract_metadata()
        
        if self.file_type != 'xlsx':
            return metadata  # Only xlsx supports openpyxl metadata
        
        try:
            wb = load_workbook(self.file_path, read_only=True)
            props = wb.properties
            if props.title:
                metadata['file_title'] = props.title
            if props.creator:
                metadata['author'] = props.creator
            if props.created:
                metadata['creation_date'] = int(props.created.timestamp())
            if props.modified:
                metadata['last_update_date'] = int(props.modified.timestamp())
            wb.close()
        except Exception as e:
            logger.error(f"[{self.file_path}] XLSX metadata extraction failed: {e}")
        
        return metadata
