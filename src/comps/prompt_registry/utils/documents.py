# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from beanie import Document


class PromptDocument(Document):
    prompt_text: str
    filename: str

    class Settings:
        name = "prompt_collection"

    class Config:
        schema_extra = {
            "example": {
                "prompt_text": "What is AMX?",
                "filename": "test_filename.txt",
            }
        }