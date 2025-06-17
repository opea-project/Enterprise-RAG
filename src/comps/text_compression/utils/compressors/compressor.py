# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any

class Compressor(ABC):
    """
    Abstract Compressor class.
    """
    @abstractmethod
    async def compress_text(self, txt: str, file_info: str, **kwargs: Any) -> str:
        """
        Compress the given text.

        Parameters:
        - txt (str): The text to compress.
        - **kwargs: Optional additional parameters.

        Returns:
        - str: The compressed text.

        """
        raise NotImplementedError
