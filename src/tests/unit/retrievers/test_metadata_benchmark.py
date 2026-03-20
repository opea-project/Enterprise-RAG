#!/usr/bin/env python3
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Metadata Extraction Test & Benchmark Suite

Unified test and benchmark script for the metadata filtering pipeline.
Combines unit tests with performance validation and visualization.

Features:
  - Unit tests for all components (pytest compatible)
  - Benchmark validation against JSON test prompts
  - 6 performance metrics with targets
  - NER latency benchmarking (with mock support)
  - Markdown report generation
  - Visualization plots (PNG)

Performance Targets:
  - Regex extraction: <25ms per query
  - NER extraction: <200ms per query
  - Date normalization: <10ms per query
  - Filter building: <10ms per query
  - Total pipeline: <250ms (with NER), <50ms (regex-only)
  - Precision: ≥85%, Recall: ≥80%, F1-Score: ≥82%

Usage:
  # Run as pytest
  pytest test_metadata_benchmark.py -v

  # Run benchmark with report generation
  python test_metadata_benchmark.py --benchmark --output-dir ./reports

  # Run with NER endpoint
  python test_metadata_benchmark.py --benchmark --ner-endpoint http://localhost:9001

  # Quick sample run
  python test_metadata_benchmark.py --benchmark --sample 10
"""

import argparse
import asyncio
import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# Setup path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from comps.retrievers.utils.models import ExtractedMetadata, spans_overlap
from comps.retrievers.utils.extractors.regex_extractor import RegexExtractor
from comps.retrievers.utils.normalizers.date_normalizer import DateNormalizer
from comps.retrievers.utils.normalizers.name_normalizer import NameNormalizer
from comps.retrievers.utils.builders.filter_expression_builder import (
    FilterExpressionBuilder,
)

# Optional imports for NER and plotting
try:
    from comps.retrievers.utils.extractors.ner_extractor import NERExtractor

    NER_AVAILABLE = True
except ImportError:
    NER_AVAILABLE = False

try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available, visualization disabled")

# ============================================================================
# Configuration
# ============================================================================

TEST_PROMPTS_DIR = Path(__file__).parent
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "reports"

PERFORMANCE_TARGETS = {
    "precision": 0.85,
    "recall": 0.80,
    "f1_score": 0.82,
    "total_latency_p99_ms": 250.0,  # With NER
    "regex_only_latency_p99_ms": 50.0,  # Without NER
    "regex_latency_p99_ms": 25.0,
    "ner_latency_p99_ms": 200.0,
    "date_norm_latency_p99_ms": 10.0,
    "name_norm_latency_p99_ms": 5.0,
    "filter_build_latency_p99_ms": 10.0,
}

TRACKED_FIELDS = [
    "author",
    "file_title",
    "creation_date",
    "ingestion_date",
    "last_update_date",
]
TRACKED_OPERATORS = [
    "==",
    ">=",
    "<=",
    "range",
    "contains",
    "OR",
    "!=",
    "fuzzy_recent",
    "fuzzy_last_year",
    "fuzzy_last_n",
    "fuzzy_this_year",
    "quarter",
    "quarter_range",
    "fuzzy_last_quarter",
]

# Fixed reference time for deterministic date normalization in benchmarks.
# All fuzzy dates ("last month", "this year", etc.) resolve relative to this.
BENCHMARK_REFERENCE_TIME = datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc)

# Date fields that need value normalization before comparison
_DATE_FIELDS = frozenset({"creation_date", "ingestion_date", "last_update_date"})


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class CaseResult:
    """Result of evaluating a single test case."""

    test_id: str
    prompt: str
    category: str
    complexity: str
    expected_fields: List[str]
    extracted_fields: List[str]
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    field_matches: Dict[str, bool] = field(default_factory=dict)
    operator_matches: Dict[str, bool] = field(default_factory=dict)
    value_matches: Dict[str, bool] = field(default_factory=dict)
    value_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Latencies (all in milliseconds)
    regex_latency_ms: float = 0.0
    ner_latency_ms: float = 0.0
    name_norm_latency_ms: float = 0.0
    norm_latency_ms: float = 0.0
    filter_latency_ms: float = 0.0
    total_latency_ms: float = 0.0

    error: Optional[str] = None


@dataclass
class BenchmarkMetrics:
    """Aggregated benchmark metrics."""

    language: str
    timestamp: str = ""
    total_cases: int = 0
    extraction_mode: str = "hybrid"  # 'regex_only', 'ner_only', or 'hybrid'

    # Core metrics
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    # Value accuracy (exact match after normalization)
    value_precision: float = 0.0
    value_recall: float = 0.0
    value_f1_score: float = 0.0

    # Latency percentiles (all in milliseconds)
    regex_latency_p50: float = 0.0
    regex_latency_p95: float = 0.0
    regex_latency_p99: float = 0.0

    ner_latency_p50: float = 0.0
    ner_latency_p95: float = 0.0
    ner_latency_p99: float = 0.0
    ner_enabled: bool = False

    norm_latency_p50: float = 0.0
    norm_latency_p95: float = 0.0
    norm_latency_p99: float = 0.0

    name_norm_latency_p50: float = 0.0
    name_norm_latency_p95: float = 0.0
    name_norm_latency_p99: float = 0.0

    filter_latency_p50: float = 0.0
    filter_latency_p95: float = 0.0
    filter_latency_p99: float = 0.0

    total_latency_p50: float = 0.0
    total_latency_p95: float = 0.0
    total_latency_p99: float = 0.0

    # Field-level accuracy
    field_accuracy: Dict[str, float] = field(default_factory=dict)
    field_value_accuracy: Dict[str, float] = field(default_factory=dict)
    field_tp: Dict[str, int] = field(default_factory=dict)
    field_fn: Dict[str, int] = field(default_factory=dict)
    field_fp: Dict[str, int] = field(default_factory=dict)
    field_value_tp: Dict[str, int] = field(default_factory=dict)

    # Operator-level accuracy
    operator_accuracy: Dict[str, float] = field(default_factory=dict)
    operator_tp: Dict[str, int] = field(default_factory=dict)
    operator_expected: Dict[str, int] = field(default_factory=dict)

    # Category breakdown
    category_accuracy: Dict[str, float] = field(default_factory=dict)
    complexity_accuracy: Dict[str, float] = field(default_factory=dict)

    # Errors
    errors: List[str] = field(default_factory=list)

    # Raw results
    results: List[CaseResult] = field(default_factory=list)


# ============================================================================
# Mock NER Extractor for Benchmarking
# ============================================================================


class MockNERExtractor:
    """Mock NER extractor that simulates latency and returns basic extractions.

    Uses simple heuristics for testing without real OVMS endpoint.
    Interface matches NERExtractor (extract returns List, latency via property).
    """

    def __init__(self, simulated_latency_ms: float = 150.0, jitter_ms: float = 30.0):
        self.simulated_latency_ms = simulated_latency_ms
        self.jitter_ms = jitter_ms
        self._last_latency_ms = 0.0

    @property
    def last_latency_ms(self) -> float:
        """Latency of the last extract() call in milliseconds."""
        return self._last_latency_ms

    def _detect_language(self, query: str) -> str:
        """Detect Polish vs English based on language-specific words."""
        polish_indicators = [
            "przez",
            "od",
            "autorstwa",
            "napisane",
            "napisany",
            "napisana",
            "stworzone",
            "stworzony",
            "stworzona",
            "dokumenty",
            "raporty",
            "znajdź",
            "pokaż",
            "wszystkie",
            "albo",
            "lub",
            "zespołu",
            "ostatnich",
            "ostatni",
            "ostatnia",
            "bieżącego",
            "ubiegłego",
            "roku",
            "miesiącach",
            "kwartale",
            "tygodniach",
        ]
        query_lower = query.lower()
        for indicator in polish_indicators:
            if indicator in query_lower:
                return "pl"
        return "en"

    async def extract(self, query: str) -> List[ExtractedMetadata]:
        """Extract with simulated latency. Returns list (same interface as NERExtractor)."""
        # Simulate latency with jitter
        latency = self.simulated_latency_ms + np.random.uniform(
            -self.jitter_ms, self.jitter_ms
        )
        latency = max(10.0, latency)  # Minimum 10ms

        await asyncio.sleep(latency / 1000.0)

        self._last_latency_ms = latency

        # Simple mock extraction: find names after prepositions and years
        extractions = []

        # Detect language
        language = self._detect_language(query)

        # Language-specific author patterns
        if language == "pl":
            # Polish patterns: "przez", "autorstwa", "od", "stworzone przez"
            author_context_pattern = r"(?:przez|autorstwa|od|napisane\s+przez|napisany\s+przez|napisana\s+przez|stworzone\s+przez|stworzony\s+przez|stworzona\s+przez)\s+(?:dr\.?\s+)?([A-ZŁŚŻŹĆĄĘŃ][a-złśżźćąęń]+(?:\s+[A-ZŁŚŻŹĆĄĘŃ][a-złśżźćąęń]+)+)"
        else:
            # English patterns: "by", "from", "authored by", "written by"
            author_context_pattern = r"(?:by|from|author(?:ed)?\s+by|written\s+by|created\s+by)\s+(?:dr\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"

        for match in re.finditer(author_context_pattern, query, re.IGNORECASE):
            name = match.group(1)
            # Get the actual name span, not the whole match
            name_start = match.start(1)
            name_end = match.end(1)
            extractions.append(
                ExtractedMetadata(
                    field="author",
                    value=name,
                    operator="==",
                    confidence=0.80,
                    source="ner",
                    span=(name_start, name_end),
                )
            )

        # Look for years (simple DATE detection)
        year_pattern = r"\b(19\d{2}|20\d{2})\b"
        for match in re.finditer(year_pattern, query):
            year = match.group(1)
            extractions.append(
                ExtractedMetadata(
                    field="creation_date",
                    value=year,
                    operator="range",
                    confidence=0.85,
                    source="ner",
                    span=match.span(),
                )
            )

        # Look for titles in quotes (WORK_OF_ART detection)
        # Supports ASCII and Unicode smart/curly quotes
        title_pattern = r"""['"\u2018\u2019\u201c\u201d\u00ab\u00bb\u201e]([^'"\u2018\u2019\u201c\u201d\u00ab\u00bb\u201e]+)['"\u2018\u2019\u201c\u201d\u00ab\u00bb\u201e]"""
        for match in re.finditer(title_pattern, query):
            title = match.group(1)
            extractions.append(
                ExtractedMetadata(
                    field="file_title",
                    value=title,
                    operator="contains",
                    confidence=0.85,
                    source="ner",
                    span=(match.start(1), match.end(1)),
                )
            )

        return extractions


# ============================================================================
# Benchmark Runner
# ============================================================================


class MetadataBenchmark:
    """Runs benchmark validation against test prompts.

    Supports three extraction modes:
    - regex_only: Only regex extraction (fastest, high precision)
    - ner_only: Only NER extraction (broader coverage for informal queries)
    - hybrid: Both regex and NER (default, regex takes priority on overlaps)
    """

    def __init__(
        self,
        language: str = "en",
        ner_endpoint: Optional[str] = None,
        ner_timeout_ms: int = 200,
        ner_model_name: str = 'tanaos-NER-v1',
        simulate_ner: bool = False,
        simulated_ner_latency_ms: float = 150.0,
        extraction_mode: str = "hybrid",
        prompts_version: str = "",
        verbose: bool = False,
    ):
        self.language = language
        self.verbose = verbose
        self.extraction_mode = extraction_mode
        self.prompts_version = prompts_version

        # Determine which extractors are active based on mode
        self.regex_enabled = extraction_mode in ("regex_only", "hybrid")
        self.ner_enabled = extraction_mode in ("ner_only", "hybrid")
        self.simulate_ner = simulate_ner and self.ner_enabled

        # Initialize components - always load date_context, months, time_units from pattern files
        # Even in NER-only mode, we need these for date normalization
        _pattern_loader = RegexExtractor(language=language)
        date_context = _pattern_loader.date_context

        if self.regex_enabled:
            self.regex_extractor = _pattern_loader
        else:
            self.regex_extractor = None

        self.date_normalizer = DateNormalizer(
            date_context=date_context,
            months=_pattern_loader.get_months(),
            time_units=_pattern_loader.get_time_units(),
            reference_time=BENCHMARK_REFERENCE_TIME,
        )
        self.name_normalizer = NameNormalizer(language=language)
        self.filter_builder = FilterExpressionBuilder(connector=None)

        # NER extractor
        if self.ner_enabled:
            if simulate_ner:
                self.ner_extractor = MockNERExtractor(
                    simulated_latency_ms=simulated_ner_latency_ms
                )
            elif ner_endpoint and NER_AVAILABLE:
                self.ner_extractor = NERExtractor(
                    endpoint=ner_endpoint,
                    timeout_ms=ner_timeout_ms,
                    model_name=ner_model_name
                )
            else:
                # Stub for testing NER-only mode without real OVMS
                self.ner_extractor = MockNERExtractor(
                    simulated_latency_ms=simulated_ner_latency_ms
                )
        else:
            self.ner_extractor = None

    def load_test_cases(self) -> List[Dict[str, Any]]:
        """Load test cases from JSON file."""
        lang_suffix = "english" if self.language == "en" else "polish"
        # Handle prompts_version with or without underscore prefix
        version_suffix = self.prompts_version
        if version_suffix and not version_suffix.startswith("_"):
            version_suffix = f"_{version_suffix}"
        filename = f"test_prompts_{lang_suffix}{version_suffix}.json"
        filepath = TEST_PROMPTS_DIR / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Test file not found: {filepath}")

        data = json.loads(filepath.read_text())
        return data.get("test_cases", [])

    async def evaluate_single(self, test_case: Dict[str, Any]) -> CaseResult:
        """Evaluate a single test case with full pipeline."""
        test_id = test_case.get("id", "unknown")
        prompt = test_case.get("prompt", "")
        expected = test_case.get("expected_extraction", {})
        category = test_case.get("category", "unknown")
        complexity = test_case.get("complexity", "unknown")

        result = CaseResult(
            test_id=test_id,
            prompt=prompt,
            category=category,
            complexity=complexity,
            expected_fields=list(expected.keys()),
            extracted_fields=[],
        )

        try:
            # Stage 1: Regex extraction (if enabled)
            if self.regex_enabled and self.regex_extractor:
                start = time.perf_counter()
                regex_extractions = self.regex_extractor.extract(prompt)
                result.regex_latency_ms = (time.perf_counter() - start) * 1000
            else:
                regex_extractions = []

            # Stage 2: NER extraction (if enabled)
            ner_extractions = []
            if self.ner_enabled and self.ner_extractor:
                start = time.perf_counter()
                ner_extractions = await self.ner_extractor.extract(prompt)
                # Use last_latency_ms if available (MockNERExtractor, NERExtractor), else wall clock
                result.ner_latency_ms = getattr(
                    self.ner_extractor,
                    "last_latency_ms",
                    (time.perf_counter() - start) * 1000,
                )

            # Merge extractions (regex takes priority)
            all_extractions = self._merge_extractions(
                regex_extractions, ner_extractions
            )

            # Stage 3: Date normalization
            start = time.perf_counter()
            normalized = self.date_normalizer.normalize(all_extractions, prompt)
            result.norm_latency_ms = (time.perf_counter() - start) * 1000

            # Stage 3.5: Name normalization (Polish author lemmatization)
            start = time.perf_counter()
            normalized = self.name_normalizer.normalize(normalized)
            result.name_norm_latency_ms = (time.perf_counter() - start) * 1000

            # Stage 4: Filter building
            start = time.perf_counter()
            _ = self.filter_builder.build(normalized)
            result.filter_latency_ms = (time.perf_counter() - start) * 1000

            # Total latency
            result.total_latency_ms = (
                result.regex_latency_ms
                + result.ner_latency_ms
                + result.name_norm_latency_ms
                + result.norm_latency_ms
                + result.filter_latency_ms
            )

            # Evaluate accuracy
            extracted_by_field: Dict[str, List[ExtractedMetadata]] = defaultdict(list)
            for ext in normalized:
                extracted_by_field[ext.field].append(ext)
                if ext.field not in result.extracted_fields:
                    result.extracted_fields.append(ext.field)

            # Mapping of fuzzy operators to their normalized form
            # Fuzzy operators get normalized to 'range' or '>=' by DateNormalizer
            FUZZY_OPERATOR_NORMALIZED = {
                "fuzzy_recent": "range",
                "fuzzy_last_year": "range",
                "fuzzy_this_year": "range",
                "fuzzy_last_quarter": "range",
                "fuzzy_last_n": "range",
                "quarter": "range",
                "quarter_range": "range",
            }

            # Evaluate each expected field
            for field_name, expected_val in expected.items():
                expected_op = expected_val.get("operator", "==")

                if expected_op not in result.operator_matches:
                    result.operator_matches[expected_op] = False

                if field_name in extracted_by_field:
                    result.field_matches[field_name] = True
                    result.true_positives += 1

                    # Check operator match - also check normalized form for fuzzy operators
                    expected_normalized = FUZZY_OPERATOR_NORMALIZED.get(
                        expected_op, expected_op
                    )
                    for ext in extracted_by_field[field_name]:
                        if (
                            ext.operator == expected_op
                            or ext.operator == expected_normalized
                        ):
                            result.operator_matches[expected_op] = True
                            break

                    # Value matching: compare extracted value with expected
                    exp_value = expected_val.get("value") or expected_val.get("values")
                    if exp_value is not None:
                        # For date fields, normalise the expected value to
                        # timestamps (same transform the pipeline applies)
                        # so the comparison is apples-to-apples.
                        compare_value = exp_value
                        if field_name in _DATE_FIELDS:
                            compare_value = self._normalize_expected_date_value(
                                field_name, exp_value, expected_op
                            )
                            # After normalisation the operator may have changed
                            # (e.g. fuzzy_last_n → range).  Use the normalised
                            # operator for the comparison.
                            compare_op = FUZZY_OPERATOR_NORMALIZED.get(
                                expected_op, expected_op
                            )
                        else:
                            compare_op = expected_op

                        extracted_vals = extracted_by_field[field_name]
                        value_matched = self._check_value_match(
                            extracted_vals, compare_value, compare_op
                        )
                        result.value_matches[field_name] = value_matched
                        # Store details for reporting
                        got_values = [ext.value for ext in extracted_vals]
                        result.value_details[field_name] = {
                            "expected": compare_value,
                            "got": got_values[0]
                            if len(got_values) == 1
                            else got_values,
                            "matched": value_matched,
                        }
                else:
                    result.field_matches[field_name] = False
                    result.false_negatives += 1

            # Count false positives
            for field_name in extracted_by_field:
                if field_name not in expected:
                    result.false_positives += 1

        except Exception as e:
            result.error = str(e)

        return result

    @staticmethod
    def _check_value_match(
        extracted: List[ExtractedMetadata],
        expected_value: Any,
        expected_op: str,
    ) -> bool:
        """Compare extracted values against expected.

        For '==' and 'contains': compare single string values.
        For 'OR': compare sets of values (order-independent).
        For 'range'/'>='/'<=': compare numeric/date values.
        For '!=': compare exclusion value.
        """
        got_values = [ext.value for ext in extracted]

        # Normalize to comparable forms
        def normalize_val(v):
            if isinstance(v, str):
                return v.strip().lower()
            if isinstance(v, list):
                return sorted(s.strip().lower() if isinstance(s, str) else s for s in v)
            return v

        exp_norm = normalize_val(expected_value)

        if expected_op == "OR":
            # Expected is a list. Extracted may be a single list value or multiple extractions.
            if not isinstance(expected_value, list):
                return False
            # Flatten extracted values into a set
            got_set = set()
            for v in got_values:
                if isinstance(v, list):
                    got_set.update(
                        s.strip().lower() if isinstance(s, str) else str(s) for s in v
                    )
                elif isinstance(v, str):
                    got_set.add(v.strip().lower())
                else:
                    got_set.add(str(v))
            exp_set = set(
                s.strip().lower() if isinstance(s, str) else str(s)
                for s in expected_value
            )
            return got_set == exp_set

        elif expected_op in ("range", ">=", "<="):
            # Date values: compare as-is (numeric tuples or ints)
            for ext in extracted:
                if normalize_val(ext.value) == exp_norm:
                    return True
                # Also check tuple/list equivalence
                if isinstance(ext.value, (list, tuple)) and isinstance(
                    expected_value, (list, tuple)
                ):
                    if list(ext.value) == list(expected_value):
                        return True
            return False

        else:  # '==', 'contains', '!='
            for ext in extracted:
                if normalize_val(ext.value) == exp_norm:
                    return True
            return False

    def _normalize_expected_date_value(
        self,
        field_name: str,
        expected_value: Any,
        expected_op: str,
    ) -> Any:
        """Compute the expected post-normalization date value.

        The test data stores symbolic expected values (e.g. 2022 for >=,
        'last_month' for fuzzy_last_n).  The DateNormalizer converts these
        to Unix timestamps.  We replay the same normalisation here so the
        benchmark can do a meaningful exact-match comparison.

        Returns the normalised expected value, or the original value when
        normalisation is not applicable (e.g. value is None).
        """
        if expected_value is None:
            return None

        # Build a fake ExtractedMetadata with the expected value so we can
        # feed it through the same DateNormalizer the pipeline uses.
        # Some expected values need light pre-processing to match what the
        # regex extractor would actually produce.

        raw_value: Any = expected_value
        op = expected_op

        # Convert bare int years to str (regex extractor emits strings)
        if op in (">=", "<=", "range") and isinstance(raw_value, int):
            raw_value = str(raw_value)

        # YYYY-MM shorthand (e.g. '2024-01') → month_range via DateNormalizer
        if isinstance(raw_value, str) and re.match(r"^\d{4}-\d{2}$", raw_value):
            year, month = raw_value.split("-")
            # Build a month name from the month number for the normalizer
            month_num = int(month)
            start_ts, end_ts = self.date_normalizer._month_to_timestamp_range(
                month_num, int(year)
            )
            if op == ">=":
                return start_ts
            elif op == "<=":
                return end_ts
            else:
                return (start_ts, end_ts)

        # Symbolic fuzzy values: 'last_month' → 30 days, 'last_week' → 7 days
        # Compute directly instead of relying on DateNormalizer to parse
        # language-specific unit words.
        if op == "fuzzy_last_n" and isinstance(raw_value, str):
            _sym_days = {
                "last_month": 30,
                "last_week": 7,
            }
            days = _sym_days.get(raw_value.lower())
            if days is not None:
                start_ts = self.date_normalizer._days_ago_timestamp(days)
                end_ts = self.date_normalizer._now_timestamp()
                return (start_ts, end_ts)

        # 'this_month' symbolic → compute range for current month
        if isinstance(raw_value, str) and raw_value.lower() == "this_month":
            ref = self.date_normalizer.now
            start_ts, end_ts = self.date_normalizer._month_to_timestamp_range(
                ref.month, ref.year
            )
            if op == ">=":
                return start_ts
            return (start_ts, end_ts)

        # Symbolic single-value operators that DateNormalizer handles directly
        # (fuzzy_recent, fuzzy_last_year, fuzzy_this_year, fuzzy_last_quarter)
        # → keep raw_value as-is; DateNormalizer reads only the operator.

        fake_ext = ExtractedMetadata(
            field=field_name,
            value=raw_value,
            operator=op,
            confidence=1.0,
            source="expected",
            span=(0, 1),
        )

        normalized = self.date_normalizer.normalize([fake_ext], query="")
        if not normalized:
            return expected_value  # normalizer dropped it → keep original
        return normalized[0].value

    def _merge_extractions(
        self,
        regex_results: List[ExtractedMetadata],
        ner_results: List[ExtractedMetadata],
    ) -> List[ExtractedMetadata]:
        """Merge regex and NER extractions (regex wins on overlap)."""
        if not ner_results:
            return regex_results

        merged = list(regex_results)
        regex_spans = [r.span for r in regex_results]

        for ner in ner_results:
            if not spans_overlap(ner.span, regex_spans):
                merged.append(ner)

        return merged

    async def run(self, sample_size: Optional[int] = None) -> BenchmarkMetrics:
        """Run full benchmark and compute metrics."""
        test_cases = self.load_test_cases()

        if sample_size and sample_size < len(test_cases):
            test_cases = test_cases[:sample_size]

        metrics = BenchmarkMetrics(
            language=self.language,
            timestamp=datetime.now().isoformat(),
            total_cases=len(test_cases),
            extraction_mode=self.extraction_mode,
            ner_enabled=self.ner_enabled,
        )

        # Initialize counters
        total_tp = 0
        total_fp = 0
        total_fn = 0

        regex_latencies = []
        ner_latencies = []
        name_norm_latencies = []
        norm_latencies = []
        filter_latencies = []
        total_latencies = []

        field_stats = {
            f: {"tp": 0, "fp": 0, "fn": 0, "expected": 0, "value_tp": 0}
            for f in TRACKED_FIELDS
        }
        operator_stats = {op: {"tp": 0, "expected": 0} for op in TRACKED_OPERATORS}
        category_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        complexity_stats = defaultdict(lambda: {"correct": 0, "total": 0})

        # Evaluate each test case
        for tc in test_cases:
            result = await self.evaluate_single(tc)
            metrics.results.append(result)

            if result.error:
                metrics.errors.append(f"{result.test_id}: {result.error}")
                continue

            # Aggregate counts
            total_tp += result.true_positives
            total_fp += result.false_positives
            total_fn += result.false_negatives

            # Latencies
            regex_latencies.append(result.regex_latency_ms)
            if result.ner_latency_ms > 0:
                ner_latencies.append(result.ner_latency_ms)
            name_norm_latencies.append(result.name_norm_latency_ms)
            norm_latencies.append(result.norm_latency_ms)
            filter_latencies.append(result.filter_latency_ms)
            total_latencies.append(result.total_latency_ms)

            # Field-level stats
            expected = tc.get("expected_extraction", {})
            for field_name in TRACKED_FIELDS:
                if field_name in expected:
                    field_stats[field_name]["expected"] += 1
                    if result.field_matches.get(field_name, False):
                        field_stats[field_name]["tp"] += 1
                        # Track value match
                        if result.value_matches.get(field_name, False):
                            field_stats[field_name]["value_tp"] += 1
                    else:
                        field_stats[field_name]["fn"] += 1
                elif field_name in result.extracted_fields:
                    field_stats[field_name]["fp"] += 1

            # Operator-level stats
            for field_name, exp_val in expected.items():
                op = exp_val.get("operator", "==")
                if op in operator_stats:
                    operator_stats[op]["expected"] += 1
                    if result.operator_matches.get(op, False):
                        operator_stats[op]["tp"] += 1

            # Category and complexity stats
            is_correct = result.false_negatives == 0 and result.false_positives == 0
            category_stats[result.category]["total"] += 1
            complexity_stats[result.complexity]["total"] += 1
            if is_correct:
                category_stats[result.category]["correct"] += 1
                complexity_stats[result.complexity]["correct"] += 1

        # Compute precision, recall, F1 (field detection level)
        if total_tp + total_fp > 0:
            metrics.precision = total_tp / (total_tp + total_fp)
        if total_tp + total_fn > 0:
            metrics.recall = total_tp / (total_tp + total_fn)
        if metrics.precision + metrics.recall > 0:
            metrics.f1_score = (
                2
                * (metrics.precision * metrics.recall)
                / (metrics.precision + metrics.recall)
            )

        # Compute value-level precision, recall, F1
        # A "value TP" means both the field was found AND the value matches expected.
        total_value_tp = sum(s["value_tp"] for s in field_stats.values())
        if total_value_tp + total_fp > 0:
            metrics.value_precision = total_value_tp / (total_value_tp + total_fp)
        if total_value_tp + total_fn > 0:
            metrics.value_recall = total_value_tp / (total_value_tp + total_fn)
        if metrics.value_precision + metrics.value_recall > 0:
            metrics.value_f1_score = (
                2
                * (metrics.value_precision * metrics.value_recall)
                / (metrics.value_precision + metrics.value_recall)
            )

        # Compute latency percentiles
        if regex_latencies:
            metrics.regex_latency_p50 = float(np.percentile(regex_latencies, 50))
            metrics.regex_latency_p95 = float(np.percentile(regex_latencies, 95))
            metrics.regex_latency_p99 = float(np.percentile(regex_latencies, 99))

        if ner_latencies:
            metrics.ner_latency_p50 = float(np.percentile(ner_latencies, 50))
            metrics.ner_latency_p95 = float(np.percentile(ner_latencies, 95))
            metrics.ner_latency_p99 = float(np.percentile(ner_latencies, 99))

        if norm_latencies:
            metrics.norm_latency_p50 = float(np.percentile(norm_latencies, 50))
            metrics.norm_latency_p95 = float(np.percentile(norm_latencies, 95))
            metrics.norm_latency_p99 = float(np.percentile(norm_latencies, 99))

        if name_norm_latencies:
            metrics.name_norm_latency_p50 = float(
                np.percentile(name_norm_latencies, 50)
            )
            metrics.name_norm_latency_p95 = float(
                np.percentile(name_norm_latencies, 95)
            )
            metrics.name_norm_latency_p99 = float(
                np.percentile(name_norm_latencies, 99)
            )

        if filter_latencies:
            metrics.filter_latency_p50 = float(np.percentile(filter_latencies, 50))
            metrics.filter_latency_p95 = float(np.percentile(filter_latencies, 95))
            metrics.filter_latency_p99 = float(np.percentile(filter_latencies, 99))

        if total_latencies:
            metrics.total_latency_p50 = float(np.percentile(total_latencies, 50))
            metrics.total_latency_p95 = float(np.percentile(total_latencies, 95))
            metrics.total_latency_p99 = float(np.percentile(total_latencies, 99))

        # Compute field-level accuracy
        for field_name, stats in field_stats.items():
            if stats["expected"] > 0:
                metrics.field_accuracy[field_name] = stats["tp"] / stats["expected"]
                metrics.field_value_accuracy[field_name] = (
                    stats["value_tp"] / stats["expected"]
                )
            metrics.field_tp[field_name] = stats["tp"]
            metrics.field_fp[field_name] = stats["fp"]
            metrics.field_fn[field_name] = stats["fn"]
            metrics.field_value_tp[field_name] = stats["value_tp"]

        # Compute operator-level accuracy
        for op, stats in operator_stats.items():
            if stats["expected"] > 0:
                metrics.operator_accuracy[op] = stats["tp"] / stats["expected"]
            metrics.operator_tp[op] = stats["tp"]
            metrics.operator_expected[op] = stats["expected"]

        # Category and complexity accuracy
        for cat, stats in category_stats.items():
            if stats["total"] > 0:
                metrics.category_accuracy[cat] = stats["correct"] / stats["total"]

        for comp, stats in complexity_stats.items():
            if stats["total"] > 0:
                metrics.complexity_accuracy[comp] = stats["correct"] / stats["total"]

        return metrics


# ============================================================================
# Report Generation
# ============================================================================


def generate_markdown_report(
    metrics_list: List[BenchmarkMetrics], output_path: Path
) -> None:
    """Generate markdown report from benchmark metrics."""

    report = []
    report.append("# Metadata Extraction Benchmark Report\n")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("**Performance Targets**: P≥85%, R≥80%, F1≥82%, Latency P99<250ms\n")
    report.append("\n---\n")

    for metrics in metrics_list:
        lang_name = "English" if metrics.language == "en" else "Polish"
        mode_name = metrics.extraction_mode.replace("_", " ").title()
        report.append(
            f"\n## {lang_name} ({metrics.language.upper()}) - {mode_name} Mode\n"
        )
        report.append(f"- Total test cases: {metrics.total_cases}\n")
        report.append(f"- Extraction mode: **{metrics.extraction_mode}**\n")
        report.append(f"- NER enabled: {metrics.ner_enabled}\n")
        report.append(f"- Errors: {len(metrics.errors)}\n")

        # Core Metrics
        report.append("\n### Core Metrics (Field Detection)\n")
        report.append("| Metric | Value | Target | Status |\n")
        report.append("|--------|-------|--------|--------|\n")

        prec_ok = metrics.precision >= PERFORMANCE_TARGETS["precision"]
        rec_ok = metrics.recall >= PERFORMANCE_TARGETS["recall"]
        f1_ok = metrics.f1_score >= PERFORMANCE_TARGETS["f1_score"]

        report.append(
            f"| Precision | {metrics.precision:.2%} | ≥{PERFORMANCE_TARGETS['precision']:.0%} | {'✅' if prec_ok else '❌'} |\n"
        )
        report.append(
            f"| Recall | {metrics.recall:.2%} | ≥{PERFORMANCE_TARGETS['recall']:.0%} | {'✅' if rec_ok else '❌'} |\n"
        )
        report.append(
            f"| F1-Score | {metrics.f1_score:.2%} | ≥{PERFORMANCE_TARGETS['f1_score']:.0%} | {'✅' if f1_ok else '❌'} |\n"
        )

        # Value Accuracy Metrics
        report.append("\n### Value Accuracy (Exact Match after Normalization)\n")
        report.append("| Metric | Value |\n")
        report.append("|--------|-------|\n")
        report.append(f"| Value Precision | {metrics.value_precision:.2%} |\n")
        report.append(f"| Value Recall | {metrics.value_recall:.2%} |\n")
        report.append(f"| Value F1-Score | {metrics.value_f1_score:.2%} |\n")

        # Latency Metrics
        report.append("\n### Latency Metrics (milliseconds)\n")
        report.append("| Component | P50 | P95 | P99 | Target | Status |\n")
        report.append("|-----------|-----|-----|-----|--------|--------|\n")

        regex_ok = (
            metrics.regex_latency_p99 <= PERFORMANCE_TARGETS["regex_latency_p99_ms"]
        )
        report.append(
            f"| Regex | {metrics.regex_latency_p50:.2f} | {metrics.regex_latency_p95:.2f} | {metrics.regex_latency_p99:.2f} | <{PERFORMANCE_TARGETS['regex_latency_p99_ms']:.0f} | {'✅' if regex_ok else '❌'} |\n"
        )

        if metrics.ner_enabled:
            ner_ok = (
                metrics.ner_latency_p99 <= PERFORMANCE_TARGETS["ner_latency_p99_ms"]
            )
            report.append(
                f"| NER | {metrics.ner_latency_p50:.2f} | {metrics.ner_latency_p95:.2f} | {metrics.ner_latency_p99:.2f} | <{PERFORMANCE_TARGETS['ner_latency_p99_ms']:.0f} | {'✅' if ner_ok else '❌'} |\n"
            )
        else:
            report.append(
                f"| NER | N/A | N/A | N/A | <{PERFORMANCE_TARGETS['ner_latency_p99_ms']:.0f} | ⏸️ (disabled) |\n"
            )

        norm_ok = (
            metrics.norm_latency_p99 <= PERFORMANCE_TARGETS["date_norm_latency_p99_ms"]
        )
        name_norm_ok = (
            metrics.name_norm_latency_p99
            <= PERFORMANCE_TARGETS["name_norm_latency_p99_ms"]
        )
        filter_ok = (
            metrics.filter_latency_p99
            <= PERFORMANCE_TARGETS["filter_build_latency_p99_ms"]
        )

        report.append(
            f"| Date Norm | {metrics.norm_latency_p50:.2f} | {metrics.norm_latency_p95:.2f} | {metrics.norm_latency_p99:.2f} | <{PERFORMANCE_TARGETS['date_norm_latency_p99_ms']:.0f} | {'✅' if norm_ok else '❌'} |\n"
        )
        report.append(
            f"| Name Norm | {metrics.name_norm_latency_p50:.2f} | {metrics.name_norm_latency_p95:.2f} | {metrics.name_norm_latency_p99:.2f} | <{PERFORMANCE_TARGETS['name_norm_latency_p99_ms']:.0f} | {'✅' if name_norm_ok else '❌'} |\n"
        )
        report.append(
            f"| Filter Build | {metrics.filter_latency_p50:.2f} | {metrics.filter_latency_p95:.2f} | {metrics.filter_latency_p99:.2f} | <{PERFORMANCE_TARGETS['filter_build_latency_p99_ms']:.0f} | {'✅' if filter_ok else '❌'} |\n"
        )

        target = (
            PERFORMANCE_TARGETS["total_latency_p99_ms"]
            if metrics.ner_enabled
            else PERFORMANCE_TARGETS["regex_only_latency_p99_ms"]
        )
        total_ok = metrics.total_latency_p99 <= target
        report.append(
            f"| **Total** | {metrics.total_latency_p50:.2f} | {metrics.total_latency_p95:.2f} | {metrics.total_latency_p99:.2f} | <{target:.0f} | {'✅' if total_ok else '❌'} |\n"
        )

        # Field-level Accuracy
        report.append("\n### Field-level Accuracy\n")
        report.append("| Field | Detection | Value Match | TP | Val TP | FN | FP |\n")
        report.append("|-------|-----------|-------------|----|----|----|----|----|\n")

        for field_name in TRACKED_FIELDS:
            if (
                field_name in metrics.field_accuracy
                or metrics.field_tp.get(field_name, 0)
                + metrics.field_fn.get(field_name, 0)
                > 0
            ):
                acc = metrics.field_accuracy.get(field_name, 0.0)
                val_acc = metrics.field_value_accuracy.get(field_name, 0.0)
                tp = metrics.field_tp.get(field_name, 0)
                val_tp = metrics.field_value_tp.get(field_name, 0)
                fn = metrics.field_fn.get(field_name, 0)
                fp = metrics.field_fp.get(field_name, 0)
                report.append(
                    f"| {field_name} | {acc:.2%} | {val_acc:.2%} | {tp} | {val_tp} | {fn} | {fp} |\n"
                )

        # Operator-level Accuracy
        report.append("\n### Operator-level Accuracy\n")
        report.append("| Operator | Accuracy | Correct | Expected |\n")
        report.append("|----------|----------|---------|----------|\n")

        for op in TRACKED_OPERATORS:
            if metrics.operator_expected.get(op, 0) > 0:
                acc = metrics.operator_accuracy.get(op, 0.0)
                tp = metrics.operator_tp.get(op, 0)
                exp = metrics.operator_expected.get(op, 0)
                report.append(f"| `{op}` | {acc:.2%} | {tp} | {exp} |\n")

        # Category Breakdown
        if metrics.category_accuracy:
            report.append("\n### Category Breakdown\n")
            report.append("| Category | Accuracy |\n")
            report.append("|----------|----------|\n")
            for cat, acc in sorted(metrics.category_accuracy.items()):
                report.append(f"| {cat} | {acc:.2%} |\n")

        # Complexity Breakdown
        if metrics.complexity_accuracy:
            report.append("\n### Complexity Breakdown\n")
            report.append("| Complexity | Accuracy |\n")
            report.append("|------------|----------|\n")
            for comp, acc in sorted(metrics.complexity_accuracy.items()):
                report.append(f"| {comp} | {acc:.2%} |\n")

        # Errors
        if metrics.errors:
            report.append("\n### Errors\n")
            for err in metrics.errors[:10]:
                report.append(f"- {err}\n")
            if len(metrics.errors) > 10:
                report.append(f"- ... and {len(metrics.errors) - 10} more\n")

        # Value Mismatches (diagnostic detail)
        mismatches = []
        for r in metrics.results:
            for fname, details in r.value_details.items():
                if not details.get("matched", True):
                    mismatches.append((r.test_id, fname, details))

        if mismatches:
            report.append(f"\n### Value Mismatches ({len(mismatches)} cases)\n")
            report.append("| Test ID | Field | Expected | Got |\n")
            report.append("|---------|-------|----------|-----|\n")
            for tid, fname, details in mismatches[:30]:
                exp = str(details["expected"])[:50]
                got = str(details["got"])[:50]
                report.append(f"| {tid} | {fname} | {exp} | {got} |\n")
            if len(mismatches) > 30:
                report.append(f"\n*... and {len(mismatches) - 30} more mismatches*\n")

    # Summary
    report.append("\n---\n")
    report.append("\n## Summary\n")

    all_passed = True
    for metrics in metrics_list:
        lang_name = "English" if metrics.language == "en" else "Polish"
        passed = (
            metrics.precision >= PERFORMANCE_TARGETS["precision"]
            and metrics.recall >= PERFORMANCE_TARGETS["recall"]
            and metrics.f1_score >= PERFORMANCE_TARGETS["f1_score"]
        )
        all_passed &= passed
        status = "✅ PASS" if passed else "❌ FAIL"
        report.append(
            f"- **{lang_name}**: {status} (P={metrics.precision:.1%}, R={metrics.recall:.1%}, F1={metrics.f1_score:.1%})\n"
        )
        report.append(
            f"  - Value accuracy: VP={metrics.value_precision:.1%}, VR={metrics.value_recall:.1%}, VF1={metrics.value_f1_score:.1%}\n"
        )

    report.append(
        f"\n**Overall**: {'✅ ALL TARGETS MET' if all_passed else '❌ SOME TARGETS NOT MET'}\n"
    )

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(report))
    print(f"Report saved to: {output_path}")


# ============================================================================
# Visualization
# ============================================================================


def generate_visualization(
    metrics_list: List[BenchmarkMetrics], output_path: Path
) -> None:
    """Generate visualization plots from benchmark metrics with shared legend."""

    if not MATPLOTLIB_AVAILABLE:
        print("Warning: matplotlib not available, skipping visualization")
        return

    # Create figure with GridSpec for shared legend
    fig = plt.figure(figsize=(16, 14))
    gs = fig.add_gridspec(4, 2, height_ratios=[1, 1, 1, 0.12], hspace=0.35, wspace=0.25)

    # Color scheme: Language determines base color, Mode determines shade
    # English: Blue shades (lighter for regex, medium for NER, darker for hybrid)
    # Polish: Red shades (lighter for regex, medium for NER, darker for hybrid)
    lang_mode_colors = {
        ("en", "regex_only"): "#87CEEB",  # Light blue (sky)
        ("en", "ner_only"): "#4169E1",  # Medium blue (royal)
        ("en", "hybrid"): "#00008B",  # Dark blue (navy)
        ("pl", "regex_only"): "#FFA07A",  # Light red (salmon)
        ("pl", "ner_only"): "#DC143C",  # Medium red (crimson)
        ("pl", "hybrid"): "#8B0000",  # Dark red (dark red)
    }

    # No hatching needed - colors now differentiate both language and mode

    # Collect unique (lang, mode) combinations
    unique_combos = []
    for m in metrics_list:
        combo = (m.language, m.extraction_mode)
        if combo not in unique_combos:
            unique_combos.append(combo)

    width = 0.8 / max(len(unique_combos), 1)

    # Title with modes and prompts info
    modes_in_data = list(set(m.extraction_mode for m in metrics_list))
    langs_in_data = list(set(m.language.upper() for m in metrics_list))
    # Use cases from first result (all same prompts file = same count per language)
    cases_per_lang = metrics_list[0].total_cases if metrics_list else 0
    mode_str = ", ".join(m.replace("_", " ").title() for m in sorted(modes_in_data))
    lang_str = "+".join(sorted(langs_in_data))
    fig.suptitle(
        f"Metadata Extraction Benchmark — Value Match (Exact After Normalization)\n{lang_str} | {mode_str} | n={cases_per_lang} prompts per language",
        fontsize=14,
        fontweight="bold",
    )

    # === 1. Core Metrics ===
    ax1 = fig.add_subplot(gs[0, 0])
    x = np.arange(3)
    for i, metrics in enumerate(metrics_list):
        values = [
            metrics.value_precision * 100,
            metrics.value_recall * 100,
            metrics.value_f1_score * 100,
        ]
        offset = width * (i - len(metrics_list) / 2 + 0.5)
        color = lang_mode_colors.get(
            (metrics.language, metrics.extraction_mode), "#9E9E9E"
        )
        bars = ax1.bar(
            x + offset, values, width, color=color, edgecolor="black", alpha=0.9
        )
        # Annotate with value
        for bar, val in zip(bars, values):
            label = f"{val:.1f}%"
            ax1.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    target_y = PERFORMANCE_TARGETS["precision"] * 100
    ax1.axhline(y=target_y, color="r", linestyle="--", alpha=0.7)
    ax1.text(
        2.6, target_y + 2, f"{target_y:.0f}% target", color="r", fontsize=8, va="bottom"
    )
    ax1.set_ylabel("Percentage")
    ax1.set_title("Core Metrics (Value Match)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(["Precision", "Recall", "F1-Score"])
    ax1.set_ylim(0, 120)

    # === 2. Latency (LOG SCALE for visibility of small values) ===
    ax2 = fig.add_subplot(gs[0, 1])
    components = ["Regex", "NER", "DateNorm", "NameNorm", "Filter", "Total"]
    x = np.arange(len(components))
    for i, metrics in enumerate(metrics_list):
        # Use actual values, floor at 0.01 for log scale
        p99 = [
            max(metrics.regex_latency_p99, 0.01),
            max(metrics.ner_latency_p99 if metrics.ner_enabled else 0.01, 0.01),
            max(metrics.norm_latency_p99, 0.01),
            max(metrics.name_norm_latency_p99, 0.01),
            max(metrics.filter_latency_p99, 0.01),
            max(metrics.total_latency_p99, 0.01),
        ]
        offset = width * (i - len(metrics_list) / 2 + 0.5)
        color = lang_mode_colors.get(
            (metrics.language, metrics.extraction_mode), "#9E9E9E"
        )
        bars = ax2.bar(
            x + offset, p99, width, color=color, edgecolor="black", alpha=0.9
        )
        # Annotate with value
        for bar, val in zip(bars, p99):
            label = f"{val:.2f}ms" if val < 1 else f"{val:.1f}ms"
            ax2.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7,
                rotation=45,
            )
    ax2.set_yscale("log")
    # Only show total latency target threshold
    ax2.axhline(
        y=PERFORMANCE_TARGETS["total_latency_p99_ms"],
        color="darkred",
        linestyle="--",
        alpha=0.7,
        linewidth=2,
    )
    ax2.text(
        4.6,
        PERFORMANCE_TARGETS["total_latency_p99_ms"] * 1.1,
        f"{PERFORMANCE_TARGETS['total_latency_p99_ms']:.0f}ms target",
        color="darkred",
        fontsize=8,
    )
    ax2.set_ylabel("Latency (ms) - Log Scale")
    ax2.set_title("Latency by Component (P99)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(components)
    ax2.set_ylim(0.005, 500)

    # === 3. Field Value Accuracy (Exact Match) ===
    ax3 = fig.add_subplot(gs[1, 0])
    fields = TRACKED_FIELDS
    x = np.arange(len(fields))
    for i, metrics in enumerate(metrics_list):
        values = [metrics.field_value_accuracy.get(f, 0) * 100 for f in fields]
        counts = [metrics.field_value_tp.get(f, 0) for f in fields]
        expected = [
            metrics.field_tp.get(f, 0) + metrics.field_fn.get(f, 0) for f in fields
        ]
        offset = width * (i - len(metrics_list) / 2 + 0.5)
        color = lang_mode_colors.get(
            (metrics.language, metrics.extraction_mode), "#9E9E9E"
        )
        bars = ax3.bar(
            x + offset, values, width, color=color, edgecolor="black", alpha=0.9
        )
        # Annotate with value match count / expected
        for bar, val, vtp, exp in zip(bars, values, counts, expected):
            label = f"{val:.0f}%\n{vtp}/{exp}"
            ax3.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=5,
            )
    ax3.axhline(y=80, color="r", linestyle="--", alpha=0.7)
    ax3.text(len(fields) - 0.3, 82, "80% target", color="r", fontsize=8)
    ax3.set_ylabel("Accuracy (%)")
    ax3.set_title("Field Value Accuracy (Exact Match)")
    ax3.set_xticks(x)
    ax3.set_xticklabels([f.replace("_", "\n") for f in fields], fontsize=8)
    ax3.set_ylim(0, 125)

    # === 4. Operator-level Accuracy ===
    ax4 = fig.add_subplot(gs[1, 1])
    operators_with_data = [
        op
        for op in TRACKED_OPERATORS
        if any(m.operator_expected.get(op, 0) > 0 for m in metrics_list)
    ][:8]
    x = np.arange(len(operators_with_data))
    for i, metrics in enumerate(metrics_list):
        values = [
            metrics.operator_accuracy.get(op, 0) * 100 for op in operators_with_data
        ]
        counts = [metrics.operator_expected.get(op, 0) for op in operators_with_data]
        offset = width * (i - len(metrics_list) / 2 + 0.5)
        color = lang_mode_colors.get(
            (metrics.language, metrics.extraction_mode), "#9E9E9E"
        )
        bars = ax4.bar(
            x + offset, values, width, color=color, edgecolor="black", alpha=0.9
        )
        # Annotate with value and n count
        for bar, val, count in zip(bars, values, counts):
            label = f"{val:.0f}%\nn={count}"
            ax4.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=5,
            )
    ax4.axhline(y=80, color="r", linestyle="--", alpha=0.7)
    ax4.text(len(operators_with_data) - 0.3, 82, "80% target", color="r", fontsize=8)
    ax4.set_ylabel("Accuracy (%)")
    ax4.set_title("Operator-level Accuracy")
    ax4.set_xticks(x)
    ax4.set_xticklabels(operators_with_data, fontsize=7, rotation=45, ha="right")
    ax4.set_ylim(0, 125)

    # === 5. Category Breakdown ===
    ax5 = fig.add_subplot(gs[2, 0])
    categories = ["author", "date", "title", "multi_field", "fuzzy_date_extended"]
    x = np.arange(len(categories))
    for i, metrics in enumerate(metrics_list):
        values = [metrics.category_accuracy.get(c, 0) * 100 for c in categories]
        offset = width * (i - len(metrics_list) / 2 + 0.5)
        color = lang_mode_colors.get(
            (metrics.language, metrics.extraction_mode), "#9E9E9E"
        )
        bars = ax5.bar(
            x + offset, values, width, color=color, edgecolor="black", alpha=0.9
        )
        category_counts = defaultdict(int)
        for result in metrics.results:
            category_counts[result.category] += 1
        # Annotate with value and n count
        for bar, c, val in zip(bars, categories, values):
            count = category_counts.get(c, 0)
            label = f"{val:.0f}%\nn={count}"
            ax5.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=5,
            )
    ax5.axhline(y=80, color="r", linestyle="--", alpha=0.7)
    ax5.text(len(categories) - 0.3, 82, "80% target", color="r", fontsize=8)
    ax5.set_ylabel("Accuracy (%)")
    ax5.set_title("Category Breakdown")
    ax5.set_xticks(x)
    ax5.set_xticklabels([c.replace("_", "\n") for c in categories], fontsize=8)
    ax5.set_ylim(0, 125)

    # === 6. Complexity Breakdown ===
    ax6 = fig.add_subplot(gs[2, 1])
    complexities = ["simple", "medium", "high", "extreme"]
    x = np.arange(len(complexities))
    for i, metrics in enumerate(metrics_list):
        values = [metrics.complexity_accuracy.get(c, 0) * 100 for c in complexities]
        offset = width * (i - len(metrics_list) / 2 + 0.5)
        color = lang_mode_colors.get(
            (metrics.language, metrics.extraction_mode), "#9E9E9E"
        )
        bars = ax6.bar(
            x + offset, values, width, color=color, edgecolor="black", alpha=0.9
        )
        complexity_counts = defaultdict(int)
        for result in metrics.results:
            complexity_counts[result.complexity] += 1
        # Annotate with value and n count
        for bar, c, val in zip(bars, complexities, values):
            count = complexity_counts.get(c, 0)
            label = f"{val:.0f}%\nn={count}"
            ax6.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=5,
            )
    ax6.axhline(y=80, color="r", linestyle="--", alpha=0.7)
    ax6.text(len(complexities) - 0.3, 82, "80% target", color="r", fontsize=8)
    ax6.set_ylabel("Accuracy (%)")
    ax6.set_title("Complexity Breakdown")
    ax6.set_xticks(x)
    ax6.set_xticklabels(complexities)
    ax6.set_ylim(0, 125)

    # === Shared Legend ===
    ax_legend = fig.add_subplot(gs[3, :])
    ax_legend.axis("off")
    legend_handles = []
    for lang, mode in unique_combos:
        color = lang_mode_colors.get((lang, mode), "#9E9E9E")
        label = f"{lang.upper()} - {mode.replace('_', ' ').title()}"
        patch = plt.Rectangle(
            (0, 0), 1, 1, facecolor=color, edgecolor="black", alpha=0.9, label=label
        )
        legend_handles.append(patch)
    from matplotlib.lines import Line2D

    legend_handles.append(
        Line2D([0], [0], color="r", linestyle="--", alpha=0.7, label="Target threshold")
    )
    ax_legend.legend(
        handles=legend_handles,
        loc="center",
        ncol=min(len(legend_handles), 6),
        fontsize=10,
        frameon=True,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Visualization saved to: {output_path}")


# ============================================================================
# Console Output
# ============================================================================


def print_metrics(metrics: BenchmarkMetrics, verbose: bool = False):
    """Print formatted metrics to console."""
    mode_label = metrics.extraction_mode.replace("_", " ").upper()
    print("\n" + "=" * 70)
    print(f"BENCHMARK RESULTS - {metrics.language.upper()} ({mode_label})")
    print("=" * 70)
    print(f"Total test cases: {metrics.total_cases}")
    print(f"Extraction mode: {metrics.extraction_mode}")
    print(f"NER enabled: {metrics.ner_enabled}")
    print(f"Errors: {len(metrics.errors)}")

    # Core metrics
    print("\n--- CORE METRICS ---")
    prec_status = "✓" if metrics.precision >= PERFORMANCE_TARGETS["precision"] else "✗"
    rec_status = "✓" if metrics.recall >= PERFORMANCE_TARGETS["recall"] else "✗"
    f1_status = "✓" if metrics.f1_score >= PERFORMANCE_TARGETS["f1_score"] else "✗"

    print(
        f"  {prec_status} Precision:  {metrics.precision:.2%} (target: ≥{PERFORMANCE_TARGETS['precision']:.0%})"
    )
    print(
        f"  {rec_status} Recall:     {metrics.recall:.2%} (target: ≥{PERFORMANCE_TARGETS['recall']:.0%})"
    )
    print(
        f"  {f1_status} F1-Score:   {metrics.f1_score:.2%} (target: ≥{PERFORMANCE_TARGETS['f1_score']:.0%})"
    )

    # Latency metrics
    print("\n--- LATENCY METRICS (P99) ---")

    regex_ok = metrics.regex_latency_p99 <= PERFORMANCE_TARGETS["regex_latency_p99_ms"]
    print(
        f"  {'✓' if regex_ok else '✗'} Regex:      {metrics.regex_latency_p99:.2f}ms (target: <{PERFORMANCE_TARGETS['regex_latency_p99_ms']:.0f}ms)"
    )

    if metrics.ner_enabled:
        ner_ok = metrics.ner_latency_p99 <= PERFORMANCE_TARGETS["ner_latency_p99_ms"]
        print(
            f"  {'✓' if ner_ok else '✗'} NER:        {metrics.ner_latency_p99:.2f}ms (target: <{PERFORMANCE_TARGETS['ner_latency_p99_ms']:.0f}ms)"
        )
    else:
        print("  - NER:        N/A (disabled)")

    norm_ok = (
        metrics.norm_latency_p99 <= PERFORMANCE_TARGETS["date_norm_latency_p99_ms"]
    )
    name_norm_ok = (
        metrics.name_norm_latency_p99 <= PERFORMANCE_TARGETS["name_norm_latency_p99_ms"]
    )
    filter_ok = (
        metrics.filter_latency_p99 <= PERFORMANCE_TARGETS["filter_build_latency_p99_ms"]
    )

    print(
        f"  {'✓' if norm_ok else '✗'} DateNorm:   {metrics.norm_latency_p99:.2f}ms (target: <{PERFORMANCE_TARGETS['date_norm_latency_p99_ms']:.0f}ms)"
    )
    print(
        f"  {'✓' if name_norm_ok else '✗'} NameNorm:   {metrics.name_norm_latency_p99:.2f}ms (target: <{PERFORMANCE_TARGETS['name_norm_latency_p99_ms']:.0f}ms)"
    )
    print(
        f"  {'✓' if filter_ok else '✗'} Filter:     {metrics.filter_latency_p99:.2f}ms (target: <{PERFORMANCE_TARGETS['filter_build_latency_p99_ms']:.0f}ms)"
    )

    target = (
        PERFORMANCE_TARGETS["total_latency_p99_ms"]
        if metrics.ner_enabled
        else PERFORMANCE_TARGETS["regex_only_latency_p99_ms"]
    )
    total_ok = metrics.total_latency_p99 <= target
    print(
        f"  {'✓' if total_ok else '✗'} TOTAL:      {metrics.total_latency_p99:.2f}ms (target: <{target:.0f}ms)"
    )

    # Field value accuracy (exact match)
    print("\n--- FIELD VALUE ACCURACY (Exact Match) ---")
    for field_name in TRACKED_FIELDS:
        if (
            field_name in metrics.field_value_accuracy
            or metrics.field_tp.get(field_name, 0) + metrics.field_fn.get(field_name, 0)
            > 0
        ):
            val_acc = metrics.field_value_accuracy.get(field_name, 0.0)
            val_tp = metrics.field_value_tp.get(field_name, 0)
            tp = metrics.field_tp.get(field_name, 0)
            fn = metrics.field_fn.get(field_name, 0)
            total = tp + fn
            if total > 0:
                print(f"  {field_name:20s}: {val_acc:.2%} ({val_tp}/{total})")

    print("=" * 70)


# ============================================================================
# Pytest Integration
# ============================================================================

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False


if PYTEST_AVAILABLE:

    class TestExtractedMetadata:
        """Tests for ExtractedMetadata dataclass."""

        def test_valid_extraction(self):
            extraction = ExtractedMetadata(
                field="author",
                value="John Smith",
                operator="==",
                confidence=1.0,
                source="regex",
                span=(3, 13),
            )
            assert extraction.field == "author"
            assert extraction.value == "John Smith"

        def test_invalid_field_raises(self):
            with pytest.raises(ValueError):
                ExtractedMetadata(field="invalid_field", value="test", operator="==")

        def test_invalid_operator_raises(self):
            with pytest.raises(ValueError):
                ExtractedMetadata(field="author", value="test", operator="invalid_op")

    class TestRegexExtractor:
        """Tests for RegexExtractor."""

        @pytest.fixture
        def extractor_en(self):
            return RegexExtractor(language="en")

        @pytest.fixture
        def extractor_pl(self):
            return RegexExtractor(language="pl")

        def test_author_by_pattern(self, extractor_en):
            results = extractor_en.extract("Show me papers by John Smith")
            author = next((r for r in results if r.field == "author"), None)
            assert author is not None
            assert "John Smith" in author.value

        def test_date_after_pattern(self, extractor_en):
            results = extractor_en.extract("Documents after 2020")
            date = next((r for r in results if r.field == "creation_date"), None)
            assert date is not None
            assert date.operator == ">="

        def test_polish_autorstwa(self, extractor_pl):
            results = extractor_pl.extract("Dokumenty autorstwa Jana Kowalskiego")
            author = next((r for r in results if r.field == "author"), None)
            assert author is not None

    class TestDateNormalizer:
        """Tests for DateNormalizer."""

        @pytest.fixture
        def normalizer(self):
            _patterns = RegexExtractor(language="en")
            return DateNormalizer(
                date_context=_patterns.get_date_context_keywords(),
                months=_patterns.get_months(),
                time_units=_patterns.get_time_units(),
                reference_time=BENCHMARK_REFERENCE_TIME,
            )

        def test_fuzzy_recent(self, normalizer):
            extraction = ExtractedMetadata(
                field="ingestion_date", value="recently", operator="fuzzy_recent"
            )
            results = normalizer.normalize([extraction], "show recent documents")
            assert len(results) == 1
            assert results[0].operator == "range"

        def test_year_to_range(self, normalizer):
            extraction = ExtractedMetadata(
                field="creation_date", value="2024", operator="range"
            )
            results = normalizer.normalize([extraction], "documents in 2024")
            assert len(results) == 1
            assert results[0].operator == "range"


# ============================================================================
# Main Entry Point
# ============================================================================


async def run_benchmark(args):
    """Run benchmark with given arguments."""
    metrics_list = []

    languages = ["en", "pl"] if args.language == "both" else [args.language]
    modes = args.modes.split(",") if args.modes else ["regex_only"]
    prompts_version = args.prompts_version if hasattr(args, "prompts_version") else ""

    for lang in languages:
        for mode in modes:
            mode = mode.strip()
            mode_label = mode.upper().replace("_", " ")
            print(f"\n{'=' * 70}")
            print(f"Running benchmark: {lang.upper()} - {mode_label}")
            if prompts_version:
                print(f"Using prompts version: {prompts_version}")
            print(f"{'=' * 70}")

            # Determine if we need to simulate NER for this mode
            need_ner = mode in ("ner_only", "hybrid")
            simulate = args.simulate_ner and need_ner

            benchmark = MetadataBenchmark(
                language=lang,
                ner_endpoint=args.ner_endpoint,
                ner_timeout_ms=getattr(args, 'ner_timeout', 2000),
                ner_model_name=getattr(args, 'ner_model_name', 'tanaos-NER-v1'),
                simulate_ner=simulate,
                simulated_ner_latency_ms=args.ner_latency,
                extraction_mode=mode,
                prompts_version=prompts_version,
                verbose=args.verbose,
            )

            metrics = await benchmark.run(sample_size=args.sample)
            metrics_list.append(metrics)

            print_metrics(metrics, verbose=args.verbose)

    # Generate outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use CET timezone for timestamp (HH_MM format, no seconds)
    from zoneinfo import ZoneInfo

    cet_time = datetime.now(ZoneInfo("Europe/Warsaw"))
    timestamp = cet_time.strftime("%Y%m%d_%H%M")

    # Simplified file naming: only add "_difficult" suffix if using difficult prompts
    file_suffix = "difficult_" if prompts_version == "_difficult" else ""

    # Markdown report
    report_path = output_dir / f"benchmark_report_{file_suffix}{timestamp}.md"
    generate_markdown_report(metrics_list, report_path)

    # Visualization
    if MATPLOTLIB_AVAILABLE:
        plot_path = output_dir / f"benchmark_plots_{file_suffix}{timestamp}.png"
        generate_visualization(metrics_list, plot_path)

    # Generate summary outputs (hybrid-only) if hybrid mode was run
    hybrid_metrics = [m for m in metrics_list if m.extraction_mode == "hybrid"]
    if hybrid_metrics:
        summary_report_path = (
            output_dir / f"benchmark_report_summary_{file_suffix}{timestamp}.md"
        )
        generate_markdown_report(hybrid_metrics, summary_report_path)
        if MATPLOTLIB_AVAILABLE:
            summary_plot_path = (
                output_dir / f"benchmark_plots_summary_{file_suffix}{timestamp}.png"
            )
            generate_visualization(hybrid_metrics, summary_plot_path)
        print(f"Summary Report: {summary_report_path}")
        if MATPLOTLIB_AVAILABLE:
            print(f"Summary Plots:  {summary_plot_path}")

    # Summary
    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)
    print(f"Report: {report_path}")
    if MATPLOTLIB_AVAILABLE:
        print(f"Plots:  {plot_path}")

    # Return success status
    all_passed = all(
        m.precision >= PERFORMANCE_TARGETS["precision"]
        and m.recall >= PERFORMANCE_TARGETS["recall"]
        and m.f1_score >= PERFORMANCE_TARGETS["f1_score"]
        for m in metrics_list
    )

    return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(
        description="Metadata Extraction Test & Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run pytest unit tests
  pytest test_metadata_benchmark.py -v

  # Run benchmark with regex-only (default, fastest)
  python test_metadata_benchmark.py --benchmark --modes regex_only

  # Run 3-way comparison (regex, NER, hybrid)
  python test_metadata_benchmark.py --benchmark --modes regex_only,ner_only,hybrid --simulate-ner

  # Run with simulated NER latency
  python test_metadata_benchmark.py --benchmark --modes hybrid --simulate-ner

  # Run with actual NER endpoint
  python test_metadata_benchmark.py --benchmark --modes hybrid --ner-endpoint http://localhost:9001

  # Quick sample run
  python test_metadata_benchmark.py --benchmark --sample 10
        """,
    )
    
    parser.add_argument('--benchmark', action='store_true',
                        help='Run benchmark mode (generates report and plots)')
    parser.add_argument('--language', '-l', choices=['en', 'pl', 'both'],
                        default='both', help='Language to test')
    parser.add_argument('--modes', '-m', type=str, default='hybrid',
                        help='Extraction modes to test (comma-separated): regex_only, ner_only, hybrid')
    parser.add_argument('--prompts-version', type=str, default='',
                        help='Test prompts version suffix (e.g., "_v4" for test_prompts_english_v4.json)')
    parser.add_argument('--sample', '-s', type=int, default=None,
                        help='Number of test cases to sample')
    parser.add_argument('--output-dir', '-o', type=str,
                        default=str(DEFAULT_OUTPUT_DIR),
                        help='Output directory for reports')
    parser.add_argument('--ner-endpoint', type=str, default=None,
                        help='NER OVMS endpoint URL')
    parser.add_argument('--simulate-ner', action='store_true',
                        help='Simulate NER with mock latency (required for ner_only/hybrid without real endpoint)')
    parser.add_argument('--ner-latency', type=float, default=150.0,
                        help='Simulated NER latency in ms (default: 150)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()

    if args.benchmark:
        return asyncio.run(run_benchmark(args))
    else:
        print(
            "Use --benchmark to run benchmark mode, or run with pytest for unit tests"
        )
        print(
            "Example: python test_metadata_benchmark.py --benchmark --modes regex_only,ner_only,hybrid --simulate-ner"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
