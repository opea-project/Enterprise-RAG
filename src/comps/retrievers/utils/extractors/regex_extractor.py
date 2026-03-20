# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Regex-based metadata extractor for query parsing.

Extracts metadata constraints from user queries using configurable regex patterns.
Supports English and Polish languages with patterns defined in YAML files.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

from comps.retrievers.utils.models import ExtractedMetadata, spans_overlap
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")


class RegexExtractor:
    """Extracts metadata from queries using regex patterns.
    
    Loads patterns from YAML files and applies them to extract author, date,
    and title metadata. All patterns are compiled at initialization.
    """
    
    # Patterns directory (always relative to this file)
    PATTERNS_DIR = Path(__file__).parent / "patterns"
    
    def __init__(self, language: str = "en"):
        self.language = language
        self._patterns_path = self.PATTERNS_DIR / f"patterns_{language}.yaml"
        
        # Load and compile patterns
        self.patterns = self._load_patterns()
        self.compiled_patterns = self._compile_patterns()
        self.date_context = self._load_date_context()
        
        logger.info(f"RegexExtractor initialized with {language} patterns from {self._patterns_path}")
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load patterns from YAML file."""
        if not self._patterns_path.exists():
            raise FileNotFoundError(f"Patterns file not found: {self._patterns_path}")
        
        with open(self._patterns_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        if 'patterns' not in self._config:
            raise ValueError(f"Invalid patterns file: missing 'patterns' key in {self._patterns_path}")
        
        return self._config['patterns']
    
    def _compile_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Compile all regex patterns for each category, sorted by priority."""
        compiled = {}
        
        for category in ['author', 'date', 'title']:
            if category not in self.patterns:
                logger.warning(f"No patterns found for category: {category}")
                compiled[category] = []
                continue
            
            compiled[category] = []
            for pattern_def in self.patterns[category]:
                try:
                    # Determine regex flags
                    flags = re.IGNORECASE if pattern_def.get('flags') == 'IGNORECASE' else 0
                    
                    compiled_pattern = {
                        'name': pattern_def.get('name', 'unnamed'),
                        'regex': re.compile(pattern_def['regex'], flags),
                        'field': pattern_def['field'],
                        'operator': pattern_def['operator'],
                        'group': pattern_def.get('group'), # Single capture group
                        'groups': pattern_def.get('groups'), # Multiple capture groups
                        'priority': pattern_def.get('priority', 5),
                        'preset_value': pattern_def.get('value'),  
                    }
                    compiled[category].append(compiled_pattern)
                    
                except re.error as e:
                    logger.error(f"Failed to compile pattern '{pattern_def.get('name')}': {e}")
                    continue
            
            # Sort by priority (higher first)
            compiled[category].sort(key=lambda x: x['priority'], reverse=True)
        
        return compiled
    
    def _load_date_context(self) -> Dict[str, List[str]]:
        """Load date context keywords for field disambiguation."""
        # date_context is at root level of config, not inside patterns
        if hasattr(self, '_config') and 'date_context' in self._config:
            return self._config['date_context']
        return {
            'creation_date': [],
            'last_update_date': [],
            'ingestion_date': []
        }
    
    def extract(self, query: str) -> List[ExtractedMetadata]:
        """Extract metadata from query."""
        if not query or not query.strip():
            return []
        
        extractions: List[ExtractedMetadata] = []
        
        # Track matched spans to avoid duplicates
        matched_spans: List[tuple] = []
        
        for category in ['author', 'date', 'title']:
            category_extractions = self._extract_category(query, category, matched_spans)
            extractions.extend(category_extractions)
        
        logger.debug(f"Regex extracted {len(extractions)} metadata items from query")
        return extractions
    
    def _extract_category(
        self, 
        query: str, 
        category: str,
        matched_spans: List[tuple]
    ) -> List[ExtractedMetadata]:
        """Extract metadata for a specific category, skipping overlapping spans."""
        extractions = []
        
        for pattern in self.compiled_patterns.get(category, []):
            matches = pattern['regex'].finditer(query)
            
            for match in matches:
                span = (match.start(), match.end())
                
                # Skip if this span overlaps with already matched spans
                if spans_overlap(span, matched_spans):
                    continue
                
                # Extract value based on group configuration
                try:
                    value = self._extract_value(match, pattern)
                    if value is None:
                        continue
                    
                    extraction = ExtractedMetadata(
                        field=pattern['field'],
                        value=value,
                        operator=pattern['operator'],
                        confidence=1.0,  # Regex always has full confidence
                        source='regex',
                        span=span
                    )
                    extractions.append(extraction)
                    matched_spans.append(span)
                    
                    logger.debug(
                        f"Regex match: pattern='{pattern['name']}', "
                        f"field={extraction.field}, value={extraction.value}, "
                        f"span={span}"
                    )
                    
                except Exception as e:
                    logger.error(f"Error extracting from pattern '{pattern['name']}': {e}")
                    continue
        
        return extractions
    
    def _extract_value(self, match: re.Match, pattern: Dict) -> Optional[Any]:
        """Extract value from regex match based on pattern config (group, groups, or preset)."""
        operator = pattern['operator']
        
        # If pattern has a preset value, use it directly
        if pattern.get('preset_value') is not None:
            return pattern['preset_value']
        
        # Single group extraction
        if pattern.get('group'):
            group_num = pattern['group']
            value = match.group(group_num)
            if value:
                value = value.strip()
                # For date patterns with year, keep as string (normalize later)
                return value
            return None
        
        # Multiple groups extraction (e.g., for OR operators or ranges)
        if pattern.get('groups'):
            values = []
            for group_num in pattern['groups']:
                group_value = match.group(group_num)
                if group_value:
                    values.append(group_value.strip())
            
            if not values:
                return None
            
            # For range operator, return as tuple
            if operator == 'range' and len(values) == 2:
                return tuple(values)
            
            # For OR operator, return as list
            if operator == 'OR':
                return values
            
            return values[0] if len(values) == 1 else values
        
        # No group specified - pattern is just a marker (e.g., fuzzy_recent)
        return match.group(0).strip()
    
    def get_date_context_keywords(self) -> Dict[str, List[str]]:
        """Get date context keywords for field disambiguation."""
        return self.date_context
    
    def get_or_keywords(self) -> List[str]:
        """Get OR keywords for detecting OR relationships between entities."""
        if hasattr(self, '_config') and 'or_keywords' in self._config:
            return self._config['or_keywords']
        # Fallback defaults
        return ['or', 'and', '&', ',']

    def get_months(self) -> Dict[str, int]:
        """Get month name → month number mapping for DateNormalizer."""
        if hasattr(self, '_config') and 'months' in self._config:
            return self._config['months']
        return {}

    def get_time_units(self) -> Dict[str, int]:
        """Get time unit word → day multiplier mapping for DateNormalizer."""
        if hasattr(self, '_config') and 'time_units' in self._config:
            return self._config['time_units']
        return {}
