# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import io
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from fastapi import UploadFile
from comps.hierarchical_dataprep.utils.hierarchical_indexer import HierarchicalIndexer

class TestHierarchicalIndexer(unittest.TestCase):

    def setUp(self):
        self.chunk_size = 100
        self.chunk_overlap = 10
        self.vllm_endpoint = "http://localhost:8000"
        self.summary_model = "summary-model"
        self.max_new_tokens = 50

        self.indexer = HierarchicalIndexer(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            vllm_endpoint=self.vllm_endpoint,
            summary_model=self.summary_model,
            max_new_tokens=self.max_new_tokens
        )

    @patch("comps.cores.utils.utils.sanitize_env")
    @patch("os.path.exists")
    @patch("os.chmod")
    def test_save_file_to_local_disk(self, mock_os_chmod, mock_os_exists, mock_sanitize_env):
        mock_sanitize_env.return_value = "/tmp/opea_upload"
        mock_os_exists.return_value = False
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.file = io.BytesIO(b"file_content")
        mock_file.read.return_value = b"file content"

        save_path, doc_id = self.indexer._save_file_to_local_disk(mock_file)

        mock_os_chmod.assert_called_once_with("/tmp/opea_upload", 0o700)
        self.assertEqual(save_path, Path("/tmp/opea_upload/test.pdf"))
        self.assertTrue(isinstance(doc_id, str))
    
    @patch("langchain_community.llms.VLLMOpenAI")
    @patch("langchain_community.llms.VLLMOpenAI.invoke")
    def test_generate_summary(self, mock_vllm_invoke, mock_vllm_openai):
        mock_llm = MagicMock()
        mock_vllm_openai.return_value = mock_llm
        mock_vllm_invoke.return_value = "summary"

        text = "This is a test text."
        summary = self.indexer._generate_summary(text)

        mock_vllm_invoke.assert_called_once_with(self.indexer.summary_prompt.format(text=text, max_new_tokens=self.max_new_tokens))
        self.assertEqual(summary, "summary")


if __name__ == "__main__":
    unittest.main()
