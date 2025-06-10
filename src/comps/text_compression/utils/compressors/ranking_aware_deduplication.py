import re
import nltk
from typing import List, Set, Optional, Callable

from comps.text_compression.utils.compressors.compressor import Compressor
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class RankedDeduplicator(Compressor):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RankedDeduplicator, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the ranking-aware deduplicator."""
        try:
            # Download necessary NLTK resources if not already present
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
        except Exception:
            raise

    def _get_ngrams(self, text: str, n: int = 3) -> Set[str]:
        """Extract n-grams from text for fuzzy matching."""
        # Normalize text
        text = re.sub(r'\s+', ' ', text.lower()).strip()

        # Create n-grams
        tokens = text.split()
        if len(tokens) < n:
            return set(tokens)  # Return individual tokens if text is too short

        return set(' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

    def _compute_overlap(self, text1: str, text2: str, n: int = 3) -> float:
        """Compute overlap between two texts based on n-grams."""
        ngrams1 = self._get_ngrams(text1, n)
        ngrams2 = self._get_ngrams(text2, n)

        # Edge cases
        if not ngrams1 and not ngrams2:
            return 1.0  # Both empty means identical
        if not ngrams1 or not ngrams2:
            return 0.0  # One empty means no overlap

        # Calculate overlap score
        intersection = len(ngrams1.intersection(ngrams2))
        smallest_set = min(len(ngrams1), len(ngrams2))

        return intersection / smallest_set

    def _rank_segments(self, segments: List[str], rank_function: Optional[Callable] = None) -> List[float]:
        """Rank segments by importance."""
        if rank_function:
            # Use provided ranking function
            return rank_function(segments)

        # Default ranking: score based on segment length and non-stopword ratio
        try:
            from nltk.corpus import stopwords
            stopwords_set = set(stopwords.words('english'))
        except Exception:
            # If stopwords not available, use a small set of common ones
            stopwords_set = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}

        ranks = []
        for segment in segments:
            # Count words and non-stopwords
            words = re.findall(r'\b\w+\b', segment.lower())
            non_stopwords = [w for w in words if w not in stopwords_set]

            # Rank based on segment length and non-stopword ratio
            segment_length = len(segment)
            non_stopword_ratio = len(non_stopwords) / len(words) if words else 0

            # Combined score (adjust weights as needed)
            rank = 0.7 * segment_length + 0.3 * (non_stopword_ratio * segment_length)
            ranks.append(rank)

        # Normalize ranks to 0-1
        max_rank = max(ranks) if ranks else 1
        return [r / max_rank for r in ranks]

    def deduplicate(self,
                segments: List[str],
                overlap_threshold: float = 0.7,
                rank_function: Optional[Callable] = None) -> List[str]:
        """
        Deduplicate segments considering their ranking.
        Higher ranked segments are kept in case of duplicates.
        """
        logger.info(f"Starting deduplication with {len(segments)} segments")
        if len(segments) <= 1:
            return segments

        # Rank all segments
        ranks = self._rank_segments(segments, rank_function)

        # Create segment info tuples with original positions
        segment_info = [(i, segment, rank) for i, (segment, rank) in enumerate(zip(segments, ranks))]

        # Sort by rank for deduplication decisions only
        ranked_segments = sorted(segment_info, key=lambda x: x[2], reverse=True)

        # Track which original indices to keep
        keep_indices = set(range(len(segments)))

        # Find duplicates to remove
        for i, (orig_i, segment, segment_rank) in enumerate(ranked_segments):
            # Skip if this segment is already marked for removal
            if orig_i not in keep_indices:
                continue

            # Check for similar segments with lower rank
            for j, (orig_j, other_segment, other_rank) in enumerate(ranked_segments):
                if i == j or orig_j not in keep_indices:
                    continue

                # Check similarity
                overlap = self._compute_overlap(segment, other_segment)
                logger.debug(f"Overlap between segment {orig_i} and {orig_j}: {overlap:.2f}")

                # Remove lower-ranked duplicates from consideration
                if overlap > overlap_threshold and segment_rank >= other_rank:
                    logger.info(f"Removing duplicate segment {orig_j} (overlap: {overlap:.2f})")
                    keep_indices.remove(orig_j)

        # Return kept segments in their original order
        kept_segments = [segments[i] for i in sorted(keep_indices)]
        logger.info(f"Kept {len(kept_segments)}/{len(segments)} segments after deduplication")
        return kept_segments

    def compress_text(self,
                      text: str,
                      segment_type: str = "paragraph",
                      overlap_threshold: float = 0.95,
                      rank_function: Optional[Callable] = None) -> str:
        """
        Compress text by deduplicating content while preserving higher-ranked segments.

        Args:
            text (str): The text to compress.
            segment_type (str): Type of segments to process ('paragraph' or 'sentence').
            overlap_threshold (float): Threshold above which segments are considered duplicates.

        Returns:
            str: The deduplicated text.
        """
        # Split text into segments
        if segment_type.lower() == "paragraph":
            segments = [p for p in re.split(r'\n\s*\n', text) if p.strip()]
        elif segment_type.lower() == "sentence":
            segments = nltk.sent_tokenize(text)
        else:
            logger.warning(f"Unknown segment_type: {segment_type}. Using paragraph.")
            segments = [p for p in re.split(r'\n\s*\n', text) if p.strip()]

        # Deduplicate segments
        kept_segments = self.deduplicate(segments, overlap_threshold, rank_function)

        # Reconstruct text with appropriate separator
        if segment_type.lower() == "paragraph":
            return "\n\n".join(kept_segments)
        else:  # sentence
            return " ".join(kept_segments)

    def __str__(self):
        return "RankedDeduplicator Compressor"
