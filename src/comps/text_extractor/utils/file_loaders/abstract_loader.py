# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any


class AbstractLoader(ABC):
    """Base class for document loaders with text and metadata extraction."""
    
    MISSING_DATE = -1  # Sentinel for unavailable dates

    def __init__(self, file_path):
        self.file_path = file_path
        self.file_type = file_path.split('.')[-1].lower()

    @abstractmethod
    def extract_text(self):
        raise NotImplementedError

    def extract_metadata(self) -> Dict[str, Any]:
        """Extract document metadata. Override in subclasses for rich metadata.
        
        Base implementation returns filename and ingestion_date only.
        Subclasses should call super().extract_metadata() and add format-specific fields.
        """
        return {
            'filename': os.path.basename(self.file_path),
            'ingestion_date': int(datetime.now(timezone.utc).timestamp()),
        }
