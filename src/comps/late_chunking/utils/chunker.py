# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


from typing import List, Optional, Tuple
from comps import get_opea_logger

CHUNKING_STRATEGIES = ['fixed', 'sentences']

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class Chunker:
    """
    Text chunking utility for late chunking embedding workflows.

    This class provides intelligent text chunking with two strategies:
    - 'fixed': Token-based chunking with predictable, uniform chunk sizes
    - 'sentences': Semantic chunking that respects sentence boundaries

    Args:
        strategy (str): Chunking strategy - either 'fixed' or 'sentences'
        model_name (str): The name of the embedding model used to load the appropriate tokenizer.

    Raises:
        ValueError: If strategy is not supported or tokenizer cannot be loaded

    """
    def __init__(
        self,
        strategy: str,
        model_name: str
    ):

        self.chunking_strategy = strategy.lower().strip()
        if self.chunking_strategy not in CHUNKING_STRATEGIES:
            raise ValueError(f"Unsupported chunking strategy: '{self.chunking_strategy}'. Supported strategies are: {CHUNKING_STRATEGIES}")

        try:
            logger.info(f"Loading tokenizer for model: {model_name}")
            # Load tokenizer from Hugging Face Hub
            from tokenizers import Tokenizer as HFTokenizer
            try:
                self.tokenizer = HFTokenizer.from_pretrained(model_name)
            except Exception:
                # Fallback: try loading with transformers-compatible approach
                from huggingface_hub import hf_hub_download
                tokenizer_file = hf_hub_download(repo_id=model_name, filename="tokenizer.json")
                self.tokenizer = HFTokenizer.from_file(tokenizer_file)

            logger.info(f"Successfully loaded tokenizer for model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load tokenizer for model '{model_name}': {str(e)}")
            raise ValueError(f"Invalid model name or unable to load tokenizer: {model_name}. Error: {str(e)}")


    def _chunk_by_sentences(self, input_text: str, chunk_size: int = 512, overlap: int = 0):
        """
        Splits text into sentence-based chunks within token limits.

        This function tokenizes the input text, identifies sentence boundaries by detecting
        punctuation marks (periods), and then combines sentences into chunks that do not
        exceed the specified maximum token size. Optionally supports overlapping chunks
        for better context preservation.
        Args:
            input_text (str): Text to split.
            chunk_size (int, optional): Maximum number of tokens per chunk. Defaults to 512.
            overlap (int, optional): Number of tokens to overlap between consecutive
                chunks. Defaults to 0 (no overlap).
        Returns:
            tuple:
                chunks (list[str]): Text chunks within size limits.
                span_annotations (list[tuple[int, int]]): Start–end token indices for each chunk.

        """

        try:
            inputs = self.tokenizer.encode(input_text)
            token_ids = inputs.ids
            token_offsets = inputs.offsets
            punctuation_mark_id = self.tokenizer.token_to_id('.')
            sep_id = self.tokenizer.token_to_id('[SEP]')

        except Exception as e:
            logger.error(f"Failed to tokenize input text: {str(e)}")
            raise ValueError(f"Tokenization failed: {str(e)}")
        
        # Find sentence boundaries
        sentence_positions = [
            (i, int(start + 1))
            for i, (token_id, (start, end)) in enumerate(zip(token_ids, token_offsets))
            if token_id == punctuation_mark_id
            and (
                token_offsets[i + 1][0] - token_offsets[i][1] > 0
                or token_ids[i + 1] == sep_id
            )
        ]

        # Todo - check more corner cases - very long texts without sentence boundaries
        # If no sentence boundaries found, treat entire text as one sentence
        if not sentence_positions:
            logger.info("chunk_by_sentences - no sentence boundaries found, treating entire text as one chunk")
            # Return the entire text as a single chunk
            num_tokens = len(token_ids)
            return [input_text], [(0, num_tokens)]

        
        # Extract individual sentences
        individual_sentences = [
            input_text[x[1] : y[1]]
            for x, y in zip([(1, 0)] + sentence_positions[:-1], sentence_positions)
        ]
        individual_spans = [
            (x[0], y[0]) for (x, y) in zip([(1, 0)] + sentence_positions[:-1], sentence_positions)
        ]
        
        # Combine sentences into chunks respecting max_chunk_size with overlap
        chunks = []
        span_annotations = []
        
        i = 0
        while i < len(individual_sentences):
            current_chunk = ""
            current_start_token = None
            current_end_token = None
            
            # Build chunk starting from sentence i
            j = i
            while j < len(individual_sentences):
                sentence = individual_sentences[j]
                start_token, end_token = individual_spans[j]
                sentence_length = end_token - start_token
                
                # Initialize chunk
                if current_start_token is None:
                    current_chunk = sentence
                    current_start_token = start_token
                    current_end_token = end_token
                    j += 1
                # Check if adding this sentence would exceed max_chunk_size
                elif (current_end_token - current_start_token + sentence_length) <= chunk_size:
                    current_chunk += sentence
                    current_end_token = end_token
                    j += 1
                else:
                    # Can't add this sentence, break
                    break
            
            # Save the chunk
            if current_chunk:
                chunks.append(current_chunk)
                span_annotations.append((current_start_token, current_end_token))
            
            # If we've processed all sentences, we're done
            if j >= len(individual_sentences):
                break
            
            # Move to next chunk with overlap
            if overlap > 0:
                # Find the starting sentence for next chunk based on overlap
                # We want to start from a sentence that creates ~overlap tokens of overlap
                overlap_tokens = 0
                next_start_idx = j  # Default: start right after current chunk
                
                # Walk backwards from the end of current chunk to find overlap point
                for k in range(j - 1, i, -1):
                    sentence_start, sentence_end = individual_spans[k]
                    sentence_tokens = sentence_end - sentence_start
                    
                    if overlap_tokens + sentence_tokens <= overlap:
                        overlap_tokens += sentence_tokens
                        next_start_idx = k
                    else:
                        break
                
                i = next_start_idx if next_start_idx > i else j
            else:
                i = j
        
        logger.debug(f"chunk_by_sentences - created {len(chunks)} chunks from {len(individual_sentences)} sentences, max_chunk_size: {chunk_size}, overlap: {overlap}")
        
        return chunks, span_annotations


    def _chunk_by_tokens(self, text: str, chunk_size: int = 512, chunk_overlap: int = 0) -> Tuple[List[str], List[Tuple[int, int]]]:
        """
        Split text into fixed-size chunks with overlap and return chunks with span annotations.

        Divides text into token-aligned chunks of up to `chunk_size` tokens,
        optionally overlapping by `chunk_overlap` to preserve context.

        Args:
            text (str): Text to split.
            chunk_size (int, optional): Maximum number of tokens per chunk. Defaults to 512.
            chunk_overlap (int, optional): Number of tokens to overlap between consecutive
            chunks for context preservation. Must be less than chunk_size. Defaults to 0.

        Returns:
            tuple[List[str], List[Tuple[int, int]]]: A tuple containing:
            - chunks: List of text chunks
            - span_annotations: List of (start_token_pos, end_token_pos) tuples indicating
              the token positions of each chunk in the original tokenized text

        Raises:
            ValueError: if parameters are invalid
            
        """

        # Tokenize the full text to get token positions
        try:
            encoding = self.tokenizer.encode(text, add_special_tokens=False)
            token_offsets = encoding.offsets
        except AttributeError:
            raise ValueError("Tokenizer must have an 'encode' method that returns an object with 'offsets' attribute")
        except Exception as e:
            raise ValueError(f"Failed to tokenize text: {str(e)}")

        chunks = []
        span_annotations = []

        # Calculate step size (chunk_size - overlap)
        step_size = chunk_size - chunk_overlap
        num_tokens = len(token_offsets)

        # Split tokens into fixed-size chunks with overlap
        for i in range(0, num_tokens, step_size):
            start_token_pos = i
            end_token_pos = min(i + chunk_size, num_tokens)

            # Get character offsets for the chunk
            start_char = token_offsets[start_token_pos][0]
            end_char = token_offsets[end_token_pos - 1][1]

            # Extract chunk text from original text using character offsets
            chunk_text = text[start_char:end_char]
            logger.debug(f"_chunk_by_tokens - created chunk from token {start_token_pos} to {end_token_pos}: '{chunk_text}'")

            chunks.append(chunk_text)
            span_annotations.append((start_token_pos, end_token_pos))

        logger.debug(f"_chunk_by_tokens - created {len(chunks)} chunks from {num_tokens} tokens, chunk_size: {chunk_size}, chunk_overlap: {chunk_overlap}")

        return chunks, span_annotations

    def chunk(
        self,
        text: str,
        chunk_size: Optional[int] = 512,
        chunk_overlap: Optional[int] = 0,
        chunking_strategy: str = None,
    ):
        """
        Chunk text into smaller segments using the specified chunking strategy.
        """

        chunking_strategy = (chunking_strategy or self.chunking_strategy).lower().strip()


        if chunking_strategy == "fixed":
            if chunk_size < 4:
                raise ValueError("Chunk size must be >= 4.")
            return self._chunk_by_tokens(text, chunk_size, chunk_overlap)
        elif chunking_strategy == "sentences":
            return self._chunk_by_sentences(text, chunk_size, chunk_overlap)
        else:
            raise ValueError(f"Unsupported chunking strategy: '{chunking_strategy}'. Supported strategies are: {CHUNKING_STRATEGIES}")
