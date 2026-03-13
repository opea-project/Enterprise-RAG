# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader


class FallbackLoader(AbstractLoader):
    """Concrete loader that provides only basic filesystem metadata.

    Used as a fallback when the format-specific loader fails to extract metadata.
    Does not support text extraction.
    """

    def extract_text(self):
        raise NotImplementedError("FallbackLoader does not support text extraction.")
