# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Data models for metadata query parsing."""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple, Union


def spans_overlap(span: Tuple[int, int], existing_spans: List[Tuple[int, int]]) -> bool:
    """Check if span overlaps with any span in the list."""
    return any(span[0] < s[1] and span[1] > s[0] for s in existing_spans)


@dataclass
class ExtractedMetadata:
    """Single metadata constraint extracted from a query.
    
    Fields: author, file_title, creation_date, ingestion_date, last_update_date.
    Operators: ==, >=, <=, range, contains, OR, !=, and fuzzy date variants.
    """
    field: str
    value: Union[str, int, Tuple[int, int], List[str]]
    operator: str
    confidence: float = 1.0
    source: str = "regex"
    span: Tuple[int, int] = (0, 0)
    
    def __post_init__(self):
        """Validate field and operator values."""
        valid_fields = {'author', 'file_title', 'creation_date', 'ingestion_date', 'last_update_date'}
        if self.field not in valid_fields:
            raise ValueError(f"Invalid field: {self.field}. Must be one of {valid_fields}")
        
        # Standard operators plus fuzzy date operators (resolved by DateNormalizer)
        valid_operators = {
            '==', '>=', '<=', 'range', 'contains', 'OR', '!=',
            'fuzzy_recent', 'fuzzy_last_year', 'fuzzy_last_n',
            'fuzzy_this_year', 'quarter', 'quarter_range', 'fuzzy_last_quarter'
        }
        if self.operator not in valid_operators:
            raise ValueError(f"Invalid operator: {self.operator}. Must be one of {valid_operators}")


@dataclass
class QueryAnalysisResult:
    """Result of query metadata parsing with optional Redis FilterExpression."""
    filter_expression: Optional[Any] = None  # Redis FilterExpression or None
    extracted_metadata: List[ExtractedMetadata] = field(default_factory=list)
    original_query: str = ""
    latency_ms: float = 0.0
    
    @property
    def has_filters(self) -> bool:
        """Check if any metadata filters were extracted."""
        return self.filter_expression is not None
    
    @property
    def extraction_count(self) -> int:
        """Count of extracted metadata items."""
        return len(self.extracted_metadata)
