# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Name normalizer: lemmatizes Polish inflected author names to nominative form
using spaCy's pl_core_news_sm model. Lazy-loaded on first use (~15MB RAM).
"""

import time
from typing import List, Optional

from comps.retrievers.utils.models import ExtractedMetadata
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")

# Operators whose values are proper names worth lemmatizing.
_LEMMATIZABLE_OPERATORS = frozenset({"==", "OR", "!="})

# Suffix-based fallback when spaCy doesn't lemmatize. Longest-first order.
_SUFFIX_FALLBACKS = [
    # Masculine adjectival (-iego/-ego → -i/-y)
    ("ińskiego", "iński"),
    ("skiego", "ski"),
    ("ckiego", "cki"),
    ("dzkiego", "dzki"),
    # Feminine adjectival (-iej/-ą → -a)
    ("ińskiej", "ińska"),
    ("skiej", "ska"),
    ("ckiej", "cka"),
    ("dzkiej", "dzka"),
    ("ińską", "ińska"),
    ("ską", "ska"),
    ("cką", "cka"),
    ("dzką", "dzka"),
]


class NameNormalizer:
    """Lemmatizes Polish author names from inflected to nominative form.

    Lazy-loads spaCy model. Only instantiate when language is Polish.
    """

    def __init__(
        self,
        spacy_model_path: Optional[str] = None,
    ):
        self._model_name = spacy_model_path or "pl_core_news_sm"
        self._nlp = None  # Lazy-loaded
        self._available = True  # Assume available until proven otherwise
        self._load_time_ms: float = 0.0

    # Lazy model loading

    def _ensure_model(self) -> bool:
        """Load spaCy model on first use. Returns True if ready."""
        if self._nlp is not None:
            return True
        if not self._available:
            return False

        import spacy

        try:
            t0 = time.perf_counter()
            nlp = spacy.load(
                self._model_name,
                # Keep only the pipes needed for lemmatization
                enable=["tok2vec", "morphologizer", "lemmatizer"],
            )
            self._load_time_ms = (time.perf_counter() - t0) * 1000
            self._nlp = nlp
            logger.info(
                "NameNormalizer: loaded %s in %.1fms (pipes: %s)",
                self._model_name,
                self._load_time_ms,
                ", ".join(nlp.pipe_names),
            )
            return True
        except OSError:
            logger.warning(
                "spaCy model '%s' not found — Polish name lemmatization disabled. "
                "Install with: python -m spacy download %s",
                self._model_name,
                self._model_name,
            )
            self._available = False
            return False

    # Core lemmatization

    def _lemmatize_name(self, name: str) -> str:
        """Lemmatize a single Polish name string to nominative, preserving case."""
        if not name or not name.strip():
            return name

        doc = self._nlp(name)
        parts: list[str] = []

        # Detect feminine context for surname gender agreement
        has_feminine_context = any(
            "Gender=Fem" in str(t.morph) and t.pos_ in ("PROPN", "NOUN") for t in doc
        )

        for token in doc:
            raw = token.text
            ws = token.whitespace_  # Trailing whitespace after this token
            # Keep punctuation/whitespace and academic titles verbatim
            if token.is_punct or token.is_space:
                parts.append(raw + ws)
                continue
            if raw.rstrip(".").lower() in {"dr", "prof", "mgr", "inż"}:
                parts.append(raw + ws)
                continue

            lemma = token.lemma_

            # Fix spaCy quirk: adjectival surnames get -iy endings
            if token.pos_ == "ADJ" and lemma.endswith("iy"):
                lemma = lemma[:-1]  # -skiy → -ski, -ckiy → -cki

            # Suffix fallback for non-nominative cases spaCy missed
            if lemma == raw and "Case=Nom" not in str(token.morph):
                for suffix, replacement in _SUFFIX_FALLBACKS:
                    if lemma.endswith(suffix):
                        lemma = lemma[: -len(suffix)] + replacement
                        break

            # Feminine surname agreement: -ski→-ska, -cki→-cka, -dzki→-dzka
            if has_feminine_context and raw != lemma and token.pos_ in ("ADJ", "PROPN"):
                for masc_suffix in ("ski", "cki", "dzki"):
                    if lemma.endswith(masc_suffix):
                        lemma = lemma[:-1] + "a"
                        break

            # Preserve original casing
            if raw[0].isupper() and lemma[0].islower():
                lemma = lemma[0].upper() + lemma[1:]
            elif raw[0].islower() and lemma[0].isupper():
                lemma = lemma[0].lower() + lemma[1:]

            parts.append(lemma + ws)

        result = "".join(parts)
        if result != name:
            logger.debug("Lemmatized name: '%s' → '%s'", name, result)
        return result

    def _lemmatize_value(self, value):
        """Lemmatize a string or list of strings."""
        if isinstance(value, list):
            return [self._lemmatize_name(v) if isinstance(v, str) else v for v in value]
        if isinstance(value, str):
            return self._lemmatize_name(value)
        return value

    # Public API

    def normalize(
        self, extractions: List[ExtractedMetadata]
    ) -> List[ExtractedMetadata]:
        """Lemmatize author values to nominative. Non-author fields pass through."""
        if not self._available:
            return extractions

        # Single-pass: find lemmatizable authors and build result in one loop.
        result: List[ExtractedMetadata] | None = None
        for i, ext in enumerate(extractions):
            needs_lemma = (
                ext.field == "author" and ext.operator in _LEMMATIZABLE_OPERATORS
            )
            if needs_lemma and result is None:
                # First author found — load model and backfill prior items.
                if not self._ensure_model():
                    return extractions
                result = list(extractions[:i])

            if result is not None:
                if needs_lemma:
                    result.append(
                        ExtractedMetadata(
                            field=ext.field,
                            value=self._lemmatize_value(ext.value),
                            operator=ext.operator,
                            confidence=ext.confidence,
                            source=ext.source,
                            span=ext.span,
                        )
                    )
                else:
                    result.append(ext)

        return result if result is not None else extractions
