# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.dataprep.utils.splitter import Splitter, SemanticSplitter
from langchain_experimental.text_splitter import SemanticChunker
from unittest.mock import Mock, patch
import numpy as np

def test_text_splitter():
    text = "Marry had a little lamb"
    s = Splitter(chunk_size=5, chunk_overlap=3)
    splitted_text = s.split_text(text)

    assert len(splitted_text) == 6
    assert splitted_text == ['Marry', 'had', 'a', 'litt', 'ittle', 'lamb']

# Custom embedding class to simulate embeddings for semantic chunking
class CustomEmbeddingModel:
    def __init__(self, embedding_dim=384):
        self.embedding_dim = embedding_dim

    def embed_documents(self, documents):
        # Simulate random embeddings for each document (sentence or chunk)
        np.random.seed(42)
        return [np.random.rand(self.embedding_dim).astype(np.float32) for _ in documents]

def test_semantic_splitter():
    text = """
    The world is rapidly changing due to advancements in technology. In particular, artificial intelligence (AI) has become a powerful tool that is reshaping industries across the globe.
    AI is being used in fields ranging from healthcare to finance, transportation, and entertainment.
    As AI systems evolve, they are becoming more capable of performing complex tasks that were once thought to require human intelligence.
    """

    mock_response = Mock()
    mock_response.json.return_value = {"embeddings": [[0.1] * 384, [0.1] * 384]}  

    # Avoid actual HTTP requests
    with patch('requests.post') as mock_post:
        mock_post.return_value = mock_response

        # Simulate returning mock embeddings for chunks
        def mock_get_text_splitter_semantic(self):
            embeddings = CustomEmbeddingModel(embedding_dim=384) 
                        
            return SemanticChunker(
                embeddings=embeddings,
                buffer_size=1,
                add_start_index=False,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=None,
                number_of_chunks=None,
                min_chunk_size=None,
            )

        
        with patch.object(SemanticSplitter, 'get_text_splitter_semantic', mock_get_text_splitter_semantic):
            semantic_splitter = SemanticSplitter(
                chunk_size=50,
                chunk_overlap=10,
                embedding_model_server="mock",
                embedding_model_server_endpoint="http://mock-endpoint",
                embedding_model_name="mock-model"
            )

     
            chunks = semantic_splitter.split_text(text)

            assert isinstance(chunks, list), f"Expected 'chunks' to be a list, but got {type(chunks)}"
            assert len(chunks) >= 2, f"Expected at least 2 chunks, but got {len(chunks)}"
            assert chunks[0].strip().startswith("The"), f"First chunk doesn't start with 'The'. First chunk: {chunks[0].strip()}"
            assert chunks[-1].strip().endswith("gence."), f"Last chunk doesn't end with 'gence.'. Last chunk: {chunks[-1].strip()}"
    
