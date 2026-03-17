# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Query Metadata Parser - Orchestrator for metadata-aware query filtering.

Coordinates regex and NER extraction, date normalization, and filter building
to construct Redis filter expressions from natural language queries.
"""

import asyncio
import os
import re
import requests
import time
from typing import Any, List, Optional

from comps.retrievers.utils.models import (
    ExtractedMetadata,
    QueryAnalysisResult,
    spans_overlap,
)
from comps.retrievers.utils.extractors import RegexExtractor, NERExtractor
from comps.retrievers.utils.extractors.ner_extractor import NERExtractorStub
from comps.retrievers.utils.normalizers import DateNormalizer, NameNormalizer
from comps.retrievers.utils.builders import FilterExpressionBuilder
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")


# Extraction modes supported by the parser
EXTRACTION_MODE_REGEX_ONLY = "regex_only"
EXTRACTION_MODE_NER_ONLY = (
    "ner_only"  # for NER model testing purposes, not recommended for actual use
)
EXTRACTION_MODE_HYBRID = "hybrid"  # Default: regex + NER

VALID_EXTRACTION_MODES = {
    EXTRACTION_MODE_REGEX_ONLY,
    EXTRACTION_MODE_NER_ONLY,
    EXTRACTION_MODE_HYBRID,
}


class QueryMetadataParser:
    """Main orchestrator for metadata-aware query parsing.

    Coordinates the parsing pipeline:
    1. Regex extraction (fast, high precision) - runs if regex_enabled
    2. NER extraction (slower, broader coverage) - runs if ner_enabled
    3. Merge extractions (prefer regex for overlapping spans)
    4. Date normalization (fuzzy dates, field disambiguation)
    5. Name normalization (language dependent)
    6. Filter expression building (construct Redis filters)

    Attributes:
        language: Language code ('en' or 'pl')
        ner_endpoint: OVMS NER endpoint URL; NER disabled if not provided
        redis_connector: Optional RedisConnector for filter building
        extraction_mode: One of 'hybrid', 'regex_only', 'ner_only'
        regex_enabled: Whether regex extraction is enabled
        ner_enabled: Whether NER extraction is enabled
    """

    def __init__(
        self,
        language: str = "en",
        ner_endpoint: Optional[str] = None,
        redis_connector: Any = None,
        extraction_mode: str = EXTRACTION_MODE_HYBRID,
        regex_enabled: Optional[bool] = None,
        ner_enabled: Optional[bool] = None,
    ):
        self.language = language.lower().strip()
        self.extraction_mode = extraction_mode.lower().strip()

        if self.extraction_mode not in VALID_EXTRACTION_MODES:
            raise ValueError(
                f"Invalid extraction_mode '{self.extraction_mode}'. "
                f"Must be one of: {', '.join(sorted(VALID_EXTRACTION_MODES))}"
            )

        # Derive extractor flags from mode (explicit overrides take precedence)
        self.regex_enabled = (
            regex_enabled
            if regex_enabled is not None
            else (
                self.extraction_mode in {EXTRACTION_MODE_REGEX_ONLY, EXTRACTION_MODE_HYBRID}
            )
        )
        self.ner_enabled = (
            ner_enabled
            if ner_enabled is not None
            else (self.extraction_mode in {EXTRACTION_MODE_NER_ONLY, EXTRACTION_MODE_HYBRID})
        )

        if not self.regex_enabled and not self.ner_enabled:
            raise ValueError("At least one extraction method must be enabled.")
        
        if not ner_endpoint:
            if self.ner_enabled:
                logger.warning(
                    "NER enabled but no endpoint provided. Using NERExtractorStub. "
                    "Set NER_ENDPOINT to connect to OVMS."
                )
            else:
                logger.info("NER disabled (NER_ENDPOINT not set), using regex-only mode")
        
        # Always load patterns (needed for date_context and OR keywords regardless of mode)
        _patterns = RegexExtractor(language=self.language)
        self._regex_extractor = _patterns if self.regex_enabled else None

        # Initialize NER extractor
        if self.ner_enabled and ner_endpoint:
            self._ner_extractor = NERExtractor(endpoint=ner_endpoint)
            self._validate_ner_endpoint(ner_endpoint)
        elif self.ner_enabled:
            self._ner_extractor = NERExtractorStub()  # For testing without OVMS
        else:
            self._ner_extractor = None

        # Date normalizer and OR detection (from pattern config)
        self._date_normalizer = DateNormalizer(
            date_context=_patterns.get_date_context_keywords(),
            months=_patterns.get_months(),
            time_units=_patterns.get_time_units(),
        )
        self._or_keywords = _patterns.get_or_keywords()
        self._max_or_gap = 50  # Max char gap between entities for OR detection

        # Pre-compile OR keyword pattern (used in merge phase)
        escaped_kws = [re.escape(k) for k in self._or_keywords]
        self._or_pattern = re.compile(
            r"\s*(?:" + "|".join(escaped_kws) + r")\s*", re.IGNORECASE
        )

        # Initialize filter builder
        self._filter_builder = FilterExpressionBuilder(connector=redis_connector)

        # Name normalizer (lemmatizes Polish names; only created for Polish)
        if self.language == "pl":
            spacy_model_path = os.getenv(
                "SPACY_MODEL_PATH"
            )  # Optional override for air-gapped deployments
            self._name_normalizer = NameNormalizer(
                spacy_model_path=spacy_model_path,
            )
        else:
            self._name_normalizer = None

        logger.info(
            f"QueryMetadataParser initialized: language={self.language}, "
            f"mode={self.extraction_mode}, regex={self.regex_enabled}, ner={self.ner_enabled}"
        )

    async def parse(self, query: str) -> QueryAnalysisResult:
        """Parse query to extract metadata and build filter expression (<250ms target)."""
        start_time = time.perf_counter()

        if not query or not query.strip():
            return QueryAnalysisResult(
                filter_expression=None,
                extracted_metadata=[],
                original_query=query,
                latency_ms=0.0,
            )

        # Phase 1: Regex extraction (runs if enabled, <25ms target)
        regex_results = []
        if self.regex_enabled and self._regex_extractor:
            regex_results = self._regex_extractor.extract(query)
            logger.debug(f"Regex extracted {len(regex_results)} items")

        # Phase 2: NER extraction (runs if enabled, <200ms target)
        ner_results = []
        if self.ner_enabled:
            ner_results = await self._extract_with_ner(query)
            logger.debug(f"NER extracted {len(ner_results)} items")

        # Phase 3: Merge extractions (+ OR detection; regex wins on overlap in hybrid mode)
        merged = self._merge_extractions(regex_results, ner_results, query)
        logger.debug(f"Merged to {len(merged)} items (with OR detection)")

        # Phase 4: Date normalization (<10ms target)
        normalized = self._date_normalizer.normalize(merged, query)
        logger.debug(f"Date-normalized to {len(normalized)} items")

        # Phase 5: Name normalization — lemmatize Polish author names (skipped for non-Polish)
        if self._name_normalizer is not None:
            normalized = self._name_normalizer.normalize(normalized)
            logger.debug(f"Name-normalized to {len(normalized)} items")

        # Phase 6: Build filter expression (<10ms target)
        filter_expression = self._filter_builder.build(normalized)

        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        result = QueryAnalysisResult(
            filter_expression=filter_expression,
            extracted_metadata=normalized,
            original_query=query,  # Keep original query unchanged
            latency_ms=latency_ms,
        )

        logger.info(
            f"Query parsed in {latency_ms:.2f}ms: "
            f"{len(normalized)} extractions, has_filter={result.has_filters}"
        )

        return result

    async def _extract_with_ner(self, query: str) -> List[ExtractedMetadata]:
        """Extract using NER with graceful degradation (empty list on failure)."""
        if not self.ner_enabled:
            return []

        try:
            return await self._ner_extractor.extract(query)
        except asyncio.TimeoutError:
            timeout = getattr(self._ner_extractor, "timeout_ms", "unknown")
            logger.warning(
                f"NER timed out after {timeout}ms, falling back to regex-only."
            )
            return []
        except Exception as e:
            logger.warning(f"NER extraction failed: {e}. Falling back to regex-only.")
            return []

    def _validate_ner_endpoint(self, endpoint: str) -> None:
        """Check if NER endpoint is responding (health check at startup)."""
        health_url = f"{endpoint.rstrip('/')}/v2/health/ready"
        try:
            resp = requests.get(health_url, timeout=5)
            if resp.status_code == 200:
                logger.info(f"NER endpoint validated: {endpoint}")
                return
        except Exception as e:
            logger.warning(
                f"NER endpoint not reachable ({health_url}): {e}. "
                "NER extraction will fall back to regex-only at query time."
            )

    def _merge_extractions(
        self,
        regex_results: List[ExtractedMetadata],
        ner_results: List[ExtractedMetadata],
        query: str = "",
    ) -> List[ExtractedMetadata]:
        """Merge regex/NER extractions (regex wins on overlap) and detect OR relationships."""
        # Step 1: Combine (regex wins on overlap)
        if not ner_results:
            combined = list(regex_results)
        elif not regex_results:
            combined = list(ner_results)
        else:
            combined = list(regex_results)
            regex_spans = [r.span for r in regex_results]
            for ner_item in ner_results:
                if not spans_overlap(ner_item.span, regex_spans):
                    combined.append(ner_item)
                else:
                    logger.debug(
                        f"Discarding overlapping NER extraction: "
                        f"field={ner_item.field}, value={ner_item.value}"
                    )

        # Step 2: Detect and merge OR relationships
        if len(combined) < 2 or not query:
            return combined

        query_lower = query.lower()

        # Group by field type
        by_field = {}
        for ext in combined:
            if ext.field not in by_field:
                by_field[ext.field] = []
            by_field[ext.field].append(ext)

        result = []
        for field, field_extractions in by_field.items():
            if len(field_extractions) < 2:
                result.extend(field_extractions)
                continue

            # Sort by span position and find OR groups
            sorted_exts = sorted(field_extractions, key=lambda x: x.span[0])
            or_groups = self._find_or_groups(sorted_exts, query_lower)

            for group in or_groups:
                if len(group) > 1:
                    merged_ext = self._merge_to_or(group)
                    result.append(merged_ext)
                    logger.info(
                        f"OR detected: merged {len(group)} {field} → {merged_ext.value}"
                    )
                else:
                    result.append(group[0])

        return result

    def _find_or_groups(
        self, sorted_extractions: List[ExtractedMetadata], query_lower: str
    ) -> List[List[ExtractedMetadata]]:
        """Find groups of extractions connected by OR keywords."""
        if not sorted_extractions:
            return []

        groups = []
        current_group = [sorted_extractions[0]]

        for i in range(1, len(sorted_extractions)):
            prev_ext = sorted_extractions[i - 1]
            curr_ext = sorted_extractions[i]

            # Check for OR keyword between them
            gap_start, gap_end = prev_ext.span[1], curr_ext.span[0]
            if 0 < gap_end - gap_start <= self._max_or_gap:
                gap_text = query_lower[gap_start:gap_end]
                if self._or_pattern.search(gap_text):
                    current_group.append(curr_ext)
                    continue

            groups.append(current_group)
            current_group = [curr_ext]

        groups.append(current_group)
        return groups

    def _merge_to_or(self, group: List[ExtractedMetadata]) -> ExtractedMetadata:
        """Merge a group of extractions into a single OR extraction."""
        values = []
        for ext in group:
            if isinstance(ext.value, list):
                values.extend(ext.value)
            else:
                values.append(ext.value)

        # Remove duplicates preserving order
        seen = set()
        unique_values = []
        for v in values:
            v_key = v.lower() if isinstance(v, str) else v
            if v_key not in seen:
                seen.add(v_key)
                unique_values.append(v)

        return ExtractedMetadata(
            field=group[0].field,
            value=unique_values,
            operator="OR",
            confidence=min(ext.confidence for ext in group),
            source="regex" if any(ext.source == "regex" for ext in group) else "ner",
            span=(min(ext.span[0] for ext in group), max(ext.span[1] for ext in group)),
        )

    def set_connector(self, connector: Any) -> None:
        """Set or update the Redis connector for filter building."""
        self._filter_builder.set_connector(connector)
        logger.debug("Redis connector updated in parser")

    @classmethod
    def from_env(cls, redis_connector: Any = None) -> "QueryMetadataParser":
        """Create parser from environment variables.

        Reads: METADATA_LANGUAGE, NER_ENDPOINT, METADATA_EXTRACTION_MODE,
        METADATA_REGEX_ENABLED, METADATA_NER_ENABLED.
        """
        language = os.getenv("METADATA_LANGUAGE", "en").lower()
        ner_endpoint = os.getenv("NER_ENDPOINT")  # Auto-enables NER if set

        # Determine extraction mode (default: hybrid if NER endpoint available, otherwise regex_only)
        default_mode = (
            EXTRACTION_MODE_HYBRID if ner_endpoint else EXTRACTION_MODE_REGEX_ONLY
        )
        extraction_mode = os.getenv("METADATA_EXTRACTION_MODE", default_mode).lower()

        # Parse optional explicit overrides
        regex_enabled = None
        ner_enabled = None

        regex_override = os.getenv("METADATA_REGEX_ENABLED")
        if regex_override is not None:
            regex_enabled = regex_override.lower() in ("true", "1", "yes")

        ner_override = os.getenv("METADATA_NER_ENABLED")
        if ner_override is not None:
            ner_enabled = ner_override.lower() in ("true", "1", "yes")

        return cls(
            language=language,
            ner_endpoint=ner_endpoint,
            redis_connector=redis_connector,
            extraction_mode=extraction_mode,
            regex_enabled=regex_enabled,
            ner_enabled=ner_enabled,
        )
