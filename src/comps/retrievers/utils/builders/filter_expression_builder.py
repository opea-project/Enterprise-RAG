# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Filter expression builder for metadata query parsing.

Uses a strategy pattern: each metadata field has its own FilterExpression class,
making it easy to add new fields by implementing FilterExpressionAbstract and
registering in SUPPORTED_FILTERS.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from comps.retrievers.utils.models import ExtractedMetadata
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class FilterExpressionAbstract(ABC):
    """Base class for per-field filter expression builders.

    Subclass this and implement ``build_filter`` to support a new metadata field.
    Provides generic ``_build_not`` (negation) and ``_combine`` (AND merge)
    so that any text-field handler can support exclusion operators.
    """

    def __init__(self, connector: Any = None):
        self._connector = connector

    @abstractmethod
    def build_filter(
        self, extractions: List[ExtractedMetadata]
    ) -> Optional[Any]:
        """Build a filter expression from one or more extractions of this field type."""
        raise NotImplementedError

    # ---- Generic helpers available to every handler ----

    def _build_not(self, field: str, value: str) -> Optional[Any]:
        """Build a negation filter for any text field via the connector."""
        if self._connector:
            try:
                return self._connector.get_text_exclude_filter_expression(field, value)
            except (ValueError, AttributeError) as e:
                logger.error(f"Failed to build exclusion filter for {field}: {e}")
                return None
        return {"type": field, "operator": "!=", "values": [value]}

    @staticmethod
    def _combine(existing: Any, new_filter: Any) -> Any:
        """Combine two filters with AND logic."""
        if existing is None:
            return new_filter
        if isinstance(existing, dict) and isinstance(new_filter, dict):
            return {"type": "combined", "operator": "AND", "filters": [existing, new_filter]}
        return existing & new_filter


# ---------------------------------------------------------------------------
# Concrete per-field builders
# ---------------------------------------------------------------------------

class FilterExpressionAuthor(FilterExpressionAbstract):
    """Author filter: multiple authors → OR, exclusions → NOT."""

    def build_filter(
        self, extractions: List[ExtractedMetadata]
    ) -> Optional[Any]:
        if not extractions:
            return None

        include_authors: List[str] = []
        exclude_authors: List[str] = []

        for ext in extractions:
            target = exclude_authors if ext.operator == "!=" else include_authors
            if isinstance(ext.value, list):
                target.extend(ext.value)
            else:
                target.append(ext.value)

        result: Any = None

        # Inclusion filter
        if include_authors and self._connector:
            try:
                result = self._connector.get_author_filter_expression(include_authors)
            except ValueError as e:
                logger.error(f"Failed to build author inclusion filter: {e}")
        elif include_authors:
            result = {
                "type": "author",
                "operator": "OR" if len(include_authors) > 1 else "==",
                "values": include_authors,
            }

        # Exclusion filter (NOT) — uses generic base-class _build_not
        for author in exclude_authors:
            exclude_filter = self._build_not("author", author)
            if exclude_filter is not None:
                result = self._combine(result, exclude_filter)

        return result


class FilterExpressionTitle(FilterExpressionAbstract):
    """Title filter: exact or contains match."""

    def build_filter(
        self, extractions: List[ExtractedMetadata]
    ) -> Optional[Any]:
        if not extractions:
            return None

        filters: List[Any] = []
        for ext in extractions:
            if not ext.value:
                continue
            title = str(ext.value)
            exact_match = ext.operator == "=="

            if self._connector:
                try:
                    f = self._connector.get_title_filter_expression(title, exact_match=exact_match)
                    filters.append(f)
                except ValueError as e:
                    logger.error(f"Failed to build title filter: {e}")
            else:
                filters.append({
                    "type": "file_title",
                    "operator": "==" if exact_match else "contains",
                    "value": title,
                })

        if not filters:
            return None
        result = filters[0]
        for f in filters[1:]:
            result = result & f if self._connector else {
                "type": "combined", "operator": "AND", "filters": [result, f]
            }
        return result


class FilterExpressionDate(FilterExpressionAbstract):
    """Date filter: range, >=, <=."""

    def build_filter(
        self, extractions: List[ExtractedMetadata]
    ) -> Optional[Any]:
        if not extractions:
            return None

        filters: List[Any] = []
        for ext in extractions:
            f = self._build_single(ext)
            if f is not None:
                filters.append(f)

        if not filters:
            return None
        result = filters[0]
        for f in filters[1:]:
            result = result & f if self._connector else {
                "type": "combined", "operator": "AND", "filters": [result, f]
            }
        return result

    def _build_single(self, extraction: ExtractedMetadata) -> Optional[Any]:
        field = extraction.field
        operator = extraction.operator
        value = extraction.value

        if self._connector:
            try:
                if operator == "range" and isinstance(value, tuple) and len(value) == 2:
                    return self._connector.get_date_range_filter_expression(
                        field, start=int(value[0]), end=int(value[1])
                    )
                elif operator == ">=":
                    return self._connector.get_date_range_filter_expression(
                        field, start=int(value)
                    )
                elif operator == "<=":
                    return self._connector.get_date_range_filter_expression(
                        field, end=int(value)
                    )
            except ValueError as e:
                logger.error(f"Failed to build date filter: {e}")
                return None
        else:
            if operator == "range" and isinstance(value, tuple):
                return {"type": field, "operator": "range", "start": value[0], "end": value[1]}
            return {"type": field, "operator": operator, "value": value}

        return None


# ---------------------------------------------------------------------------
# Registry — add new metadata fields here
# ---------------------------------------------------------------------------

SUPPORTED_FILTERS: Dict[str, Type[FilterExpressionAbstract]] = {
    "author": FilterExpressionAuthor,
    "file_title": FilterExpressionTitle,
    "creation_date": FilterExpressionDate,
    "ingestion_date": FilterExpressionDate,
    "last_update_date": FilterExpressionDate,
}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class FilterExpressionBuilder:
    """Builds combined Redis FilterExpression from normalized metadata extractions.

    Dispatches to per-field FilterExpression handlers registered in SUPPORTED_FILTERS.
    To add a new metadata field, implement FilterExpressionAbstract and register it.
    """

    def __init__(self, connector: Any = None):
        self._connector = connector
        self._filter_expressions: Dict[str, FilterExpressionAbstract] = {
            field: cls(connector=connector)
            for field, cls in SUPPORTED_FILTERS.items()
        }
        logger.debug("FilterExpressionBuilder initialized")

    def build(self, extractions: List[ExtractedMetadata]) -> Optional[Any]:
        """Build combined filter expression from extractions (AND logic)."""
        if not extractions:
            logger.debug("No extractions to build filter from")
            return None

        # Group extractions by field
        by_field: Dict[str, List[ExtractedMetadata]] = {}
        for ext in extractions:
            by_field.setdefault(ext.field, []).append(ext)

        # Build per-field filters via registered handlers
        filters: List[Any] = []
        for field, field_extractions in by_field.items():
            handler = self._filter_expressions.get(field)
            if handler is None:
                logger.debug(f"No filter handler for field '{field}', skipping")
                continue
            f = handler.build_filter(field_extractions)
            if f is not None:
                filters.append(f)

        if not filters:
            logger.debug("No valid filters built from extractions")
            return None

        combined = self._combine_filters(filters)
        logger.debug(f"Built filter expression from {len(extractions)} extractions")

        if combined is not None:
            filter_str = str(combined) if self._connector else repr(combined)
            logger.info(f"Filter expression: {filter_str}")

        return combined

    def _combine_filters(self, filters: List[Any]) -> Any:
        """Combine multiple filters with AND logic."""
        if not filters:
            return None
        if len(filters) == 1:
            return filters[0]

        if self._connector:
            result = filters[0]
            for f in filters[1:]:
                result = result & f
            return result
        return {"type": "combined", "operator": "AND", "filters": filters}

    def set_connector(self, connector: Any) -> None:
        """Set or update the Redis connector (propagates to all handlers)."""
        self._connector = connector
        for handler in self._filter_expressions.values():
            handler._connector = connector
        logger.debug("Redis connector updated")
