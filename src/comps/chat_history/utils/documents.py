# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from beanie import Document
from typing import List

from comps.cores.proto.docarray import ChatMessage

class ChatHistoryDocument(Document):
    history: List[ChatMessage]
    user_id: str
    history_name: str

    class Settings:
        name = "chat_history_collection"

    class Config:
        schema_extra = {
            "example": {
                "history": [
                    {
                        "question": "What is the capital of France?",
                        "answer": "The capital of France is Paris."
                    },
                    {
                        "question": "What is the largest planet in our solar system?",
                        "answer": "The largest planet in our solar system is Jupiter."
                    }
                ],
                "user_id": "6ff3f26b-4e9e-4f7d-a46e-584fad772435",
                "history_name": "user_session_123"
            }
        }
