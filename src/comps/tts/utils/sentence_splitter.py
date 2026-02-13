import re

from langchain_text_splitters import RecursiveCharacterTextSplitter


class SentenceAwareTextSplitter(RecursiveCharacterTextSplitter):
    """
    Custom splitter that prioritizes sentence boundaries over hard chunk size limits.
    Keeps punctuation with the previous chunk.
    """

    def split_text(self, text: str) -> list[str]:
        # First, split by sentence boundaries (. ! ? ,) using regex
        # Pattern splits after punctuation + whitespace but keeps punctuation
        pattern = r'(?<=[.!?])\s+|(?<=,)\s+'
        sentences = re.split(pattern, text.strip())

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence keeps us under chunk_size, add it
            if len(current_chunk) + len(sentence) + 1 <= self._chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                # Current chunk is full, save it and start new one
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks