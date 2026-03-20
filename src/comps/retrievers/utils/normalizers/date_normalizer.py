# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Date normalizer: resolves fuzzy dates to timestamps, converts years to ranges,
and disambiguates date fields using context keywords.

Language-agnostic: all language-specific data (month names, time unit words,
date context keywords) is loaded from YAML pattern files at initialization.
"""

import re
from calendar import monthrange
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from comps.retrievers.utils.models import ExtractedMetadata
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")

# Language-agnostic configuration constants
FUZZY_RECENT_DAYS = 30

# Roman numeral mapping (universal, not language-specific)
ROMAN_TO_INT = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'i': 1, 'ii': 2, 'iii': 3, 'iv': 4}


class DateNormalizer:
    """Normalizes date extractions to Unix timestamps with field disambiguation.

    Language-agnostic: receives month names, time unit multipliers, and date context
    keywords from YAML pattern files via constructor parameters.
    """
    def __init__(
        self,
        date_context: Optional[Dict[str, List[str]]] = None,
        months: Optional[Dict[str, int]] = None,
        time_units: Optional[Dict[str, int]] = None,
        reference_time: Optional[datetime] = None
    ):
        """Initialize with language data loaded from YAML pattern files.

        Args:
            date_context: Field disambiguation keywords (creation_date, last_update_date, ingestion_date).
            months: Month name → month number mapping (e.g. {'january': 1, 'stycznia': 1}).
            time_units: Time unit word → day multiplier mapping (e.g. {'day': 1, 'week': 7, 'dni': 1}).
            reference_time: Fixed reference time for testing (defaults to UTC now).
        """
        self.date_context = date_context or {}
        self.months = {k.lower(): v for k, v in (months or {}).items()}
        self.time_units = {k.lower(): v for k, v in (time_units or {}).items()}
        self._reference_time = reference_time

        if not self.months:
            logger.warning("DateNormalizer initialized without month names — month_range parsing disabled")
        if not self.time_units:
            logger.warning("DateNormalizer initialized without time units — fuzzy_last_n fallback to days")
    
    @property
    def now(self) -> datetime:
        """Get current reference time."""
        if self._reference_time:
            return self._reference_time
        return datetime.now(timezone.utc)
    
    def normalize(
        self, 
        extractions: List[ExtractedMetadata],
        query: str
    ) -> List[ExtractedMetadata]:
        """Normalize date extractions to timestamps; pass non-date extractions through."""
        normalized = []
        query_lower = query.lower()
        
        for extraction in extractions:
            if extraction.field in ('creation_date', 'ingestion_date', 'last_update_date'):
                try:
                    norm_extraction = self._normalize_date_extraction(extraction, query_lower)
                    if norm_extraction:
                        normalized.append(norm_extraction)
                        logger.info(
                            f"Date normalized: {extraction.operator}({extraction.value}) → "
                            f"{norm_extraction.field}:{norm_extraction.operator}({norm_extraction.value})"
                        )
                except Exception as e:
                    logger.warning(f"Failed to normalize date extraction: {e}")
                    # Skip invalid date extraction
                    continue
            else:
                # Non-date extraction - pass through unchanged
                normalized.append(extraction)
        
        return normalized
    
    def _normalize_date_extraction(
        self, 
        extraction: ExtractedMetadata,
        query_lower: str
    ) -> Optional[ExtractedMetadata]:
        """Normalize a single date extraction to Unix timestamp(s)."""
        operator = extraction.operator
        value = extraction.value
        
        # Disambiguate date field based on context
        field = self._disambiguate_date_field(extraction, query_lower)
        
        # Handle different operator types
        if operator == 'fuzzy_recent':
            # "recently" → last N days from ingestion_date
            start_ts = self._days_ago_timestamp(FUZZY_RECENT_DAYS)
            end_ts = self._now_timestamp()
            return ExtractedMetadata(
                field='ingestion_date',  # Fuzzy recent always maps to ingestion
                value=(start_ts, end_ts),
                operator='range',
                confidence=extraction.confidence,
                source=extraction.source,
                span=extraction.span
            )
        
        elif operator == 'fuzzy_last_year':
            # "last year" → previous calendar year
            last_year = self.now.year - 1
            start_ts, end_ts = self._year_to_timestamp_range(last_year)
            return ExtractedMetadata(
                field=field,
                value=(start_ts, end_ts),
                operator='range',
                confidence=extraction.confidence,
                source=extraction.source,
                span=extraction.span
            )
        
        elif operator == 'fuzzy_this_year':
            # "this year" → current calendar year
            start_ts, end_ts = self._year_to_timestamp_range(self.now.year)
            return ExtractedMetadata(
                field=field,
                value=(start_ts, end_ts),
                operator='range',
                confidence=extraction.confidence,
                source=extraction.source,
                span=extraction.span
            )
        
        elif operator == 'fuzzy_last_quarter':
            # "last quarter" → previous 3-month period
            start_ts, end_ts = self._last_quarter_range()
            return ExtractedMetadata(
                field=field,
                value=(start_ts, end_ts),
                operator='range',
                confidence=extraction.confidence,
                source=extraction.source,
                span=extraction.span
            )
        
        elif operator == 'quarter':
            # "Q3 2024" or "IV kwartał 2024" → specific quarter
            if isinstance(value, (tuple, list)) and len(value) == 2:
                # Parse quarter number (handles both Arabic and Roman numerals)
                quarter = self._parse_quarter_number(value[0], value[0])
                try:
                    year = int(value[1])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid quarter year: {value[1]}")
                    return None
                
                if quarter is None:
                    logger.warning(f"Invalid quarter number: {value[0]}")
                    return None
                    
                start_ts, end_ts = self._quarter_to_timestamp_range(quarter, year)

                # Grace period for creation_date: extend end_ts to end of next quarter to account for imprecise extraction
                if field == 'creation_date':
                    grace_q = quarter % 4 + 1          # Q3→4, Q4→1
                    grace_year = year if quarter < 4 else year + 1
                    _, end_ts = self._quarter_to_timestamp_range(grace_q, grace_year)
                    logger.debug(
                        "Quarter grace period applied: Q%d %d extended to Q%d %d end"
                        " for creation_date filter",
                        quarter, year, grace_q, grace_year,
                    )

                return ExtractedMetadata(
                    field=field,
                    value=(start_ts, end_ts),
                    operator='range',
                    confidence=extraction.confidence,
                    source=extraction.source,
                    span=extraction.span
                )
        
        elif operator == 'quarter_range':
            # Flexible quarter range 
            if isinstance(value, (tuple, list)) and len(value) >= 3:
                # Parse quarter numbers (handle Roman numerals from Polish patterns)
                start_q = self._parse_quarter_number(value[0], value[1] if len(value) > 3 else None)
                end_q = self._parse_quarter_number(value[2] if len(value) == 3 else value[2], 
                                                   value[3] if len(value) > 3 else None)
                year = int(value[-1])  # Year is always last
                
                if start_q and end_q:
                    start_ts, _ = self._quarter_to_timestamp_range(start_q, year)
                    _, end_ts = self._quarter_to_timestamp_range(end_q, year)
                    return ExtractedMetadata(
                        field=field,
                        value=(start_ts, end_ts),
                        operator='range',
                        confidence=extraction.confidence,
                        source=extraction.source,
                        span=extraction.span
                    )
        
        elif operator == 'month_range':
            # "January to March 2024" → range from start of first month to end of last month
            if isinstance(value, (tuple, list)) and len(value) >= 3:
                start_month_str, end_month_str = value[0], value[1]
                year = int(value[2])
                
                # Parse month names (from YAML-loaded month mappings)
                start_month = self.months.get(start_month_str.lower())
                end_month = self.months.get(end_month_str.lower())
                
                if start_month and end_month:
                    start_ts, _ = self._month_to_timestamp_range(start_month, year)
                    _, end_ts = self._month_to_timestamp_range(end_month, year)
                    return ExtractedMetadata(
                        field=field,
                        value=(start_ts, end_ts),
                        operator='range',
                        confidence=extraction.confidence,
                        source=extraction.source,
                        span=extraction.span
                    )
                else:
                    logger.warning(f"Invalid month range: {start_month_str} - {end_month_str}")
                    return None
        
        elif operator == 'fuzzy_last_n':
            # "last N days/weeks/months"
            if isinstance(value, (tuple, list)) and len(value) == 2:
                n, unit = value
                days = self._parse_fuzzy_last_n(n, unit)
                start_ts = self._days_ago_timestamp(days)
                end_ts = self._now_timestamp()
                return ExtractedMetadata(
                    field='ingestion_date',  # Fuzzy time period maps to ingestion
                    value=(start_ts, end_ts),
                    operator='range',
                    confidence=extraction.confidence,
                    source=extraction.source,
                    span=extraction.span
                )
        
        elif operator == 'range':
            # Year range (between X and Y) or single year (in YYYY)
            if isinstance(value, tuple) and len(value) == 2:
                start_year, end_year = value
                start_ts = self._year_start_timestamp(int(start_year))
                end_ts = self._year_end_timestamp(int(end_year))
            elif isinstance(value, str) and value.isdigit():
                # Single year treated as range
                year = int(value)
                start_ts, end_ts = self._year_to_timestamp_range(year)
            elif isinstance(value, str):
                # Try to parse as month+year (e.g., "March 2024", "marca 2024")
                parsed = self._parse_month_year(value)
                if parsed:
                    month, year = parsed
                    start_ts, end_ts = self._month_to_timestamp_range(month, year)
                else:
                    logger.warning(f"Invalid range value: {value}")
                    return None
            else:
                logger.warning(f"Invalid range value: {value}")
                return None
            
            return ExtractedMetadata(
                field=field,
                value=(start_ts, end_ts),
                operator='range',
                confidence=extraction.confidence,
                source=extraction.source,
                span=extraction.span
            )
        
        elif operator == '>=':
            # After year X
            if isinstance(value, str) and value.isdigit():
                year = int(value)
                start_ts = self._year_start_timestamp(year)
                return ExtractedMetadata(
                    field=field,
                    value=start_ts,
                    operator='>=',
                    confidence=extraction.confidence,
                    source=extraction.source,
                    span=extraction.span
                )
        
        elif operator == '<=':
            # Before year X
            if isinstance(value, str) and value.isdigit():
                year = int(value)
                end_ts = self._year_end_timestamp(year)
                return ExtractedMetadata(
                    field=field,
                    value=end_ts,
                    operator='<=',
                    confidence=extraction.confidence,
                    source=extraction.source,
                    span=extraction.span
                )
        
        # For non-date operators or already normalized values, pass through
        return extraction
    
    def _disambiguate_date_field(
        self, 
        extraction: ExtractedMetadata,
        query_lower: str
    ) -> str:
        """Determine date field from context keywords within 50-char window around span."""
        # Define localized window around the date span (50 chars before, 50 after)
        window_size = 50
        span_start = max(0, extraction.span[0] - window_size)
        span_end = min(len(query_lower), extraction.span[1] + window_size)
        localized_context = query_lower[span_start:span_end]
        
        # Check for context keywords within the localized window only
        for field, keywords in self.date_context.items():
            for keyword in keywords:
                if keyword in localized_context:
                    logger.debug(
                        f"Date field disambiguated: '{keyword}' in window "
                        f"[{span_start}:{span_end}] → {field}"
                    )
                    return field
        
        # Default to creation_date if no context found
        return extraction.field or 'creation_date'
    
    def _parse_fuzzy_last_n(self, n: str, unit: str) -> int:
        """Parse 'last N units' to total days using YAML-loaded time unit multipliers."""
        try:
            count = int(n)
        except ValueError:
            count = 1
        
        # Find multiplier from YAML-loaded time_units
        unit_lower = unit.lower()
        
        # Try exact match first
        multiplier = self.time_units.get(unit_lower)
        if multiplier is not None:
            return count * multiplier
        
        # Try prefix match (handles plural/declension variants)
        for unit_key, mult in self.time_units.items():
            if unit_lower.startswith(unit_key[:4]):
                return count * mult
        
        # Default to days
        return count
    
    def _now_timestamp(self) -> int:
        """Get current time as Unix timestamp."""
        return int(self.now.timestamp())
    
    def _days_ago_timestamp(self, days: int) -> int:
        """Get timestamp for N days ago."""
        past = self.now - timedelta(days=days)
        return int(past.timestamp())
    
    def _year_to_timestamp_range(self, year: int) -> Tuple[int, int]:
        """Convert year to (start, end) Unix timestamp range."""
        start_ts = self._year_start_timestamp(year)
        end_ts = self._year_end_timestamp(year)
        return (start_ts, end_ts)
    
    def _year_start_timestamp(self, year: int) -> int:
        """Get Unix timestamp for start of year (Jan 1 00:00:00 UTC)."""
        dt = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        return int(dt.timestamp())
    
    def _year_end_timestamp(self, year: int) -> int:
        """Get Unix timestamp for end of year (Dec 31 23:59:59 UTC)."""
        dt = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        return int(dt.timestamp())
    
    def _quarter_to_timestamp_range(self, quarter: int, year: int) -> Tuple[int, int]:
        """Convert quarter (1-4) and year to timestamp range."""
        quarter_months = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
        start_month, end_month = quarter_months.get(quarter, (1, 3))
        start = datetime(year, start_month, 1, 0, 0, 0, tzinfo=timezone.utc)
        last_day = monthrange(year, end_month)[1]
        end = datetime(year, end_month, last_day, 23, 59, 59, tzinfo=timezone.utc)
        return int(start.timestamp()), int(end.timestamp())
    
    def _parse_quarter_number(self, arabic: Optional[str], roman: Optional[str]) -> Optional[int]:
        """Parse quarter number from Arabic (1-4) or Roman (I-IV) numerals."""
        # Try Arabic numeral first
        if arabic and str(arabic).isdigit():
            q = int(arabic)
            if 1 <= q <= 4:
                return q
        
        # Try Roman numeral (check arabic param first as it might contain Roman)
        value_to_check = arabic if arabic else roman
        if value_to_check:
            value_str = str(value_to_check).upper().strip()
            q = ROMAN_TO_INT.get(value_str)
            if q:
                return q
        
        # Also check roman param
        if roman:
            value_str = str(roman).upper().strip()
            q = ROMAN_TO_INT.get(value_str)
            if q:
                return q
        
        return None
    
    def _last_quarter_range(self) -> Tuple[int, int]:
        """Get timestamp range for previous quarter."""
        current_quarter = (self.now.month - 1) // 3 + 1
        if current_quarter == 1:
            return self._quarter_to_timestamp_range(4, self.now.year - 1)
        return self._quarter_to_timestamp_range(current_quarter - 1, self.now.year)
    
    def _parse_month_year(self, text: str) -> Optional[Tuple[int, int]]:
        """Parse month+year text like 'March 2024' or 'marca 2024'."""
        if not text:
            return None
        
        text = text.strip().lower()
        
        # Try pattern: "Month YYYY" or "YYYY Month"
        # Pattern 1: Month first
        match = re.match(r'([a-zżźćąęłóńś]+)\s+(\d{4})', text, re.IGNORECASE)
        if match:
            month_str, year_str = match.groups()
            month = self.months.get(month_str.lower())
            if month:
                return (month, int(year_str))
        
        # Pattern 2: Year first
        match = re.match(r'(\d{4})\s+([a-zżźćąęłóńś]+)', text, re.IGNORECASE)
        if match:
            year_str, month_str = match.groups()
            month = self.months.get(month_str.lower())
            if month:
                return (month, int(year_str))
        
        return None
    
    def _month_to_timestamp_range(self, month: int, year: int) -> Tuple[int, int]:
        """Convert month and year to (start_timestamp, end_timestamp) range."""
        last_day = monthrange(year, month)[1]
        start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
        return int(start.timestamp()), int(end.timestamp())
