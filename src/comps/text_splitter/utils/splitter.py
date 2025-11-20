# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import re
import json
from typing import Dict, List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

from comps.text_splitter.utils.splitters.embedding_semantic import Embeddings
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class AbstractSplitter:
    """
    Abstract base class for text splitting.
    This class should not be instantiated directly.
    """
    def __init__(self):
        self.text_splitter = self.get_text_splitter()

    def get_text_splitter(self):
        """
        Returns a text splitter instance based on configuration settings.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses should implement this method")

    def split_text(self, text: str) -> List[str]:
        """
        Split input text into chunks using the configured text splitter.

        Args:
            text: The text to split

        Returns:
            List of text chunks
        """
        logger.debug(f"Splitting text of length {len(text)}")
        chunks = self.text_splitter.split_text(text)
        return chunks

class Splitter(AbstractSplitter):
    """Base splitter class using recursive character splitting."""

    def __init__(self, chunk_size: int = 100, chunk_overlap: int = 10):
        """
        Initialize the splitter with the specified chunk size and overlap.

        Args:
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Amount of overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = self.get_separators()

        super().__init__()

    def split_text(self, text: str):
        chunks = Document(page_content=text)
        docs = self.text_splitter.split_documents([chunks])
        return docs

    def get_text_splitter(self):
        """Create and return a RecursiveCharacterTextSplitter."""
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,
            separators=self.separators
        )

    @staticmethod
    def get_separators() -> List[str]:
        """
        Get the list of separators for text splitting.

        Returns:
            List of separator strings
        """
        separators = [
            "\n\n",
            "\n",
            " ",
            ".",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
            "",
        ]
        return separators

class MarkdownSplitter(AbstractSplitter):
    def __init__(self, chunk_size: int = 100, chunk_overlap: int = 10):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.md_separators = self.get_md_separators()
        self.char_separators = self.get_char_separators()

        super().__init__()

    def convert_markitdown_with_slide_headers(self, markdown_text: str) -> str:
        # Step 1: Demote all existing headers by one level
        # This ensures that original headers don't conflict with the new slide headers
        markdown_text = re.sub(r'^(#{1,6})', r'#\1', markdown_text, flags=re.MULTILINE)

        # Step 2: Convert slide number comments to Markdown headers
        markdown_text = re.sub(r'<!-- Slide number: (\d+) -->', r'# Slide \1', markdown_text)

        return markdown_text

    def strip_md_links_from_text(self, text: str) -> str:
        # Replace markdown links with just the text
        # [text](url) -> text
        text = re.sub(r'(?:\[)?([^\[\]]+)(?:\]\([^\)]+\))?', r'\1', text)
        
        # Strip asterisks from the beginning and end
        # **text** or *text* -> text
        text = text.strip('*')
        return text

    def split_text(self, text, extension: Optional[str] = None):
        splitters = self.text_splitter
        if extension in [".pptx", ".ppt"]:
            # Convert Markitdown output to Markdown with slide headers
            text = self.convert_markitdown_with_slide_headers(text)

        for splitter in splitters:
            logger.info(f"Using splitter: {splitter.__class__.__name__}")
            if isinstance(splitter, MarkdownHeaderTextSplitter):
                text = splitter.split_text(text)
            elif isinstance(splitter, RecursiveCharacterTextSplitter):
                text = splitter.split_documents(text)
            else:
                raise ValueError(f"Unsupported splitter type: {splitter.__class__.__name__}")

        # Clean metadata headers
        for doc in text:
            for key in doc.metadata:
                if key.startswith("Header"):
                    doc.metadata[key] = self.strip_md_links_from_text(doc.metadata[key])
        return text

    def get_text_splitter(self):
        md_splitter = MarkdownHeaderTextSplitter(
            self.md_separators,
            strip_headers=False
        )

        char_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.char_separators,
            add_start_index=True,
        )
        return [md_splitter, char_splitter]

    def get_char_separators(self):
        separators = [
            "\n\n",
            "\n",
            " ",
            ".",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
            "",
        ]
        return separators

    def get_md_separators(self):
        return [(f"{'#' * i}", f"Header{i}") for i in range(1, 8)]

class SemanticSplitter(AbstractSplitter):
    """Text splitter that uses semantic meaning to determine chunk boundaries."""

    def __init__(
        self,
        embedding_service_endpoint: str = "http://embedding-svc.chatqa.svc:6000/v1/embeddings",
        semantic_chunk_params_str: Optional[str] = None,
    ):
        """
        Initialize the semantic splitter.
        
        Args:
            embedding_service_endpoint: URL for the embedding service API
            semantic_chunk_params_str: JSON string containing semantic chunking parameters
        """
        self.embedding_service_endpoint = embedding_service_endpoint
        self.semantic_chunk_params = self._convert_semantic_chunk_params_to_dict(
            semantic_chunk_params_str
        )

        super().__init__()

        logger.info(
            f"Initializing Semantic Chunking with embedding service '{self.embedding_service_endpoint}'"
        )

    def get_text_splitter(self):
        """Create and return a SemanticChunker configured with the current parameters."""
        return SemanticChunker(
            embeddings = Embeddings(self.embedding_service_endpoint),
            buffer_size=self.semantic_chunk_params.get("buffer_size", 1),
            add_start_index=self.semantic_chunk_params.get("add_start_index", False),
            sentence_split_regex=self.semantic_chunk_params.get(
                "sentence_split_regex", r"(?<=[.!?])\s+"
            ),
            breakpoint_threshold_type=self.semantic_chunk_params.get(
                "breakpoint_threshold_type", "percentile"
            ),
            breakpoint_threshold_amount=self.semantic_chunk_params.get(
                "breakpoint_threshold_amount", None
            ),
            number_of_chunks=self.semantic_chunk_params.get("number_of_chunks", None),
            min_chunk_size=self.semantic_chunk_params.get("min_chunk_size", None),
        )

    @staticmethod
    def _convert_semantic_chunk_params_to_dict(semantic_chunk_params_str: Optional[str]) -> Dict:
        """
        Converts a string representation of semantic chunk parameters into a dictionary.
        
        Args:
            semantic_chunk_params_str: JSON string containing parameters
            
        Returns:
            Dictionary of parameters, empty dict if invalid input
        """
        if not semantic_chunk_params_str:
            return {}
        if semantic_chunk_params_str == "{}":
            return {}
            
        try:
            return json.loads(semantic_chunk_params_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid semantic_chunk_params format, expected JSON string, err={e}")
            raise ValueError(
                "Invalid semantic_chunk_params format. Expected JSON string."
            )
