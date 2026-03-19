# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import requests

from comps import (
    TextDoc,
    get_opea_logger,
)

from comps.cores.proto.docarray import EmbedDoc, EmbedDocList, LateChunkingInput, TextDocList
from requests.exceptions import RequestException

from comps.late_chunking.utils.chunker import Chunker 

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEALateChunking:
    def __init__(self, 
                embedding_endpoint: str = "http://embedding-svc.chatqa.svc:6000/v1/embeddings",
                model_name: str = "jinaai/jina-embeddings-v2-base-en",
                chunk_size: int = 512,
                chunk_overlap: int = 0,
                strategy: str = "sentences",
                ):
        """
        Initialize the OPEA Late Chunking service.
        
        Args:
            embedding_endpoint: URL of the embedding service endpoint
            model_name: Name of the embedding model (used for tokenizer initialization)
            chunk_size: Maximum number of tokens per chunk
            chunk_overlap: Number of tokens to overlap between consecutive chunks
            strategy: Chunking strategy ('fixed' or 'sentences')
            
        Raises:
            ValueError: If parameters are invalid or initialization fails
        """
        # Validate and store configuration
        self.embedding_endpoint = embedding_endpoint
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Validate chunk parameters
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            raise ValueError(f"chunk_size must be a positive integer, got {chunk_size}")
        
        if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be a non-negative integer, got {chunk_overlap}")
        
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})")

        try:
            logger.info(f"Initializing Chunker with strategy: {strategy}, model: {model_name}")
            self.chunker = Chunker(strategy, model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Chunker: {str(e)}")
            raise ValueError(f"Chunker initialization failed: {str(e)}")

        self._validate()
        
        # Log final configuration
        logger.info(
            f"Late Chunking microservice initialized successfully using embedding endpoint '{self.embedding_endpoint}', "
            f"tokenizer model: '{model_name}', chunking strategy: '{strategy}', "
            f"chunk size: {self.chunk_size}, chunk overlap: {self.chunk_overlap}"
        )


    def _validate(self):
        """Validate the connection to the embedding service endpoint by making a test request."""
        logger.info(f"Validating connection to embedding endpoint: {self.embedding_endpoint}")
        
        # Create a simple test document
        test_doc = TextDoc(text="This is a test document for validation.")
        test_input = TextDocList(docs=[test_doc], return_pooling=True)
        
        try:
            # Make a test request to the embedding service
            response_data = self._call_embedding_usvc(test_input)
            
            if "error" in response_data:
                raise ValueError(f"Embedding service validation failed: {response_data['error']}")
            
            # Check if we got embeddings back
            if 'docs' in response_data and len(response_data['docs']) > 0:
                logger.info(f"Successfully validated embedding endpoint: {self.embedding_endpoint}")
                logger.info("Embedding service is reachable and working.")
                return True
            else:
                raise ValueError("Embedding service returned response but no documents found")
                
        except ValueError:
            # Re-raise ValueError as is
            raise
        except Exception as e:
            logger.error(f"Failed to validate embedding endpoint {self.embedding_endpoint}: {str(e)}")
            raise ValueError(f"Cannot connect to embedding service at {self.embedding_endpoint}: {str(e)}")


    def _call_embedding_usvc(self, text_doc_list: TextDocList) -> dict:
        """Call the embedding microservice and return the response."""
        logger.info(f"Calling embedding service at {self.embedding_endpoint} with {len(text_doc_list.docs)} documents.")
        try:
            response = requests.post(
                self.embedding_endpoint,
                data=text_doc_list.model_dump_json(),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout as e:
            logger.error(f"Request timed out after 10 seconds: {str(e)}")
            return {"error": f"Request timed out: {str(e)}"}
        except requests.RequestException as e:
            logger.error(f"An error occurred while calling embedding service: {str(e)}")
            return {"error": str(e)}


    def run(self, input: LateChunkingInput) -> EmbedDocList:
        """
        Executes the late chunking embedding pipeline on a set of input documents.

        This method performs the following steps:
        1. Sends documents to the embedding service with `return_pooling=True` to obtain token-level embeddings.
        2. Splits each document into chunks using the configured chunker.
        3. Applies late chunking pooling to aggregate token embeddings for each chunk.
        4. Returns a list of embedded document chunks, each containing the chunk text, its pooled embedding, and associated metadata.

        Args:
            input (LateChunkingInput): Contains the documents to process. May include optional
                `chunk_size` and `chunk_overlap` parameters to override instance defaults.

        Returns:
            EmbedDocList: A list of embedded document chunks. Each chunk includes:
                - `text`: The chunked portion of the original document.
                - `embedding`: The pooled embedding vector for the chunk.
                - `metadata`: Metadata inherited from the original document.
        """
        all_embed_docs = []
        logger.info(f"Received request with {len(input.docs)} documents for late chunking.")
        # Create TextDocList with return_pooling enabled
        text_doc_list = TextDocList(docs=input.docs, return_pooling=True)

        try:
            response = requests.post(
                self.embedding_endpoint, 
                data=text_doc_list.model_dump_json(),
                headers={"Content-Type": "application/json"},
                timeout=180
            )
            
            if response.status_code == 200:
                response_json = response.json()
                
                # Process each document with late chunking
                for idx, doc in enumerate(response_json.get('docs', [])):
                    input_text = doc.get('text', '')
                    model_output = doc.get('embedding', [])

                    # Convert list to numpy array for _chunked_pooling
                    # The embedding should be 2D: [num_tokens, embedding_dim]
                    model_output_array = np.array(model_output)

                    # Ensure embeddings is a 2D array
                    if model_output_array.ndim == 1:
                        logger.error("Expected 2D token embeddings but got 1D")
                        raise ValueError("Expected 2D token embeddings but got 1D")
                    elif model_output_array.ndim != 2:
                        logger.error(f"Expected 2D token embeddings but got {model_output_array.ndim}D array")
                        raise ValueError(f"Expected 2D token embeddings but got {model_output_array.ndim}D array")

                    chunk_size = input.chunk_size if input.chunk_size is not None else self.chunk_size
                    chunk_overlap = input.chunk_overlap if input.chunk_overlap is not None else self.chunk_overlap
                    chunks, span_annotations = self.chunker.chunk(text=input_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)


                    # Wrap model_output in a list to match expected batch format
                    # _chunked_pooling returns [[chunk1_emb, chunk2_emb, ...]] for single doc
                    embeddings = _chunked_pooling(model_output=[model_output_array], span_annotation=[span_annotations])

                    # Validate that we got exactly one document's embeddings
                    if len(embeddings) != 1:
                        msg = f"_chunked_pooling returned embeddings for {len(embeddings)} documents, expected 1."
                        logger.error(msg)
                        raise ValueError(msg)

                    # Extract the first (and only) document's embeddings
                    embeddings = embeddings[0]

                    # Build output with chunks and their embeddings
                    for _, (chunk_text, chunk_embedding) in enumerate(zip(chunks, embeddings)):
                          
                        embed_doc = EmbedDoc(
                            text=chunk_text,
                            embedding=chunk_embedding.tolist() if isinstance(chunk_embedding, np.ndarray) else chunk_embedding,
                            metadata=doc.get('metadata', {}).copy()
                        )

                        all_embed_docs.append(embed_doc)
                        
            else:
                error_detail = "Unknown error"
                try:
                    error_response = response.json()
                    error_detail = error_response.get('detail', error_response)
                except Exception:
                    error_detail = response.text if response.text else f"HTTP {response.status_code}"
                
                logger.error(f"Embedding service returned status code {response.status_code}: {error_detail}")
                raise ValueError(f"Embedding service failed with status {response.status_code}: {error_detail}")

        except requests.Timeout as e:
            logger.error(f"Request timed out: {str(e)}")
            raise TimeoutError(f"Request timed out: {str(e)}")
        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise RequestException(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise Exception(f"Error processing: {str(e)}")

        logger.info(f"Successfully processed {len(input.docs)} documents, resulting in {len(all_embed_docs)} chunks")
        return EmbedDocList(docs=all_embed_docs)



def _chunked_pooling(
    model_output: list, span_annotation: list, max_length=None
):
    """
    Apply pooling to token embeddings based on span annotations.
    
    Args:
        model_output: List of numpy arrays containing token embeddings for each document
        span_annotation: List of lists of (start, end) tuples indicating chunk boundaries
        max_length: Optional maximum length to consider
        
    Returns:
        List of lists of pooled embeddings for each document's chunks
    """
    outputs = []
    for embeddings, annotations in zip(model_output, span_annotation):
        # Ensure embeddings is a 2D array
        if isinstance(embeddings, np.ndarray):
            if embeddings.ndim == 0:
                raise ValueError("embeddings array is 0-dimensional, cannot slice")
            elif embeddings.ndim == 1:
                raise ValueError(f"embeddings array is 1-dimensional with shape {embeddings.shape}, expected 2D [num_tokens, embedding_dim]")

        if (
            max_length is not None
        ):  # remove annotations which go beyond the max-length of the model
            annotations = [
                (start, min(end, max_length - 1))
                for (start, end) in annotations
                if start < (max_length - 1)
            ]

        pooled_embeddings = []
        for start, end in annotations:
            if (end - start) >= 1:
                token_slice = embeddings[start:end]
                pooled = token_slice.sum(axis=0) / (end - start)
                pooled_embeddings.append(pooled)

        # Convert to list if needed (numpy arrays are already in the right format)
        outputs.append(pooled_embeddings)

    return outputs