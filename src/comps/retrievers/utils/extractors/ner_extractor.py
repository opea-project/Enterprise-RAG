# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
NER-based metadata extractor for query parsing.

Uses tanaos-NER-v1 model served via OVMS to extract named entities from queries
and maps them to metadata fields (PERSON → author, DATE → dates, WORK_OF_ART → title).
"""

import asyncio
import json
import time
from typing import Dict, List, Tuple

import aiohttp

from comps.retrievers.utils.models import ExtractedMetadata
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")


# Entity type to metadata field mapping
ENTITY_FIELD_MAPPING = {
    'PERSON': 'author',
    'PER': 'author',  # Alternative label
    'DATE': 'creation_date',  # Default, may be disambiguated by DateNormalizer
    'WORK_OF_ART': 'file_title',
}


class NERExtractor:
    """
    Extracts metadata via NER model served on OVMS (KServe v2 protocol).
    Maps PERSON → author, DATE → creation_date, WORK_OF_ART → file_title
    
    Attributes:
        endpoint: OVMS endpoint URL
        timeout_ms: Request timeout in milliseconds (default: 200)
        confidence_threshold: Minimum confidence to accept entity (default: 0.7)
        last_latency_ms: Latency of the last extract() call in milliseconds
    """
    
    def __init__(
        self, 
        endpoint: str,
        timeout_ms: int = 200,
        confidence_threshold: float = 0.7,
        model_name: str = "tanaos-ner-v1"
    ):
        self.endpoint = endpoint.rstrip('/')
        self.timeout_ms = timeout_ms
        self.confidence_threshold = confidence_threshold
        self.model_name = model_name
        
        # Latency tracking for benchmarking
        self._last_latency_ms: float = 0.0
        
        # Build inference URL
        self._inference_url = f"{self.endpoint}/v2/models/{self.model_name}/infer"
        self._first_failure_logged = False
        
        logger.info(
            f"NERExtractor initialized: endpoint={self.endpoint}, "
            f"timeout={timeout_ms}ms, threshold={confidence_threshold}"
        )
    
    @property
    def last_latency_ms(self) -> float:
        """Latency of the last extract() call in milliseconds."""
        return self._last_latency_ms
    
    async def extract(self, query: str) -> List[ExtractedMetadata]:
        """Extract metadata entities from query via NER model. Returns empty list on failure."""
        if not query or not query.strip():
            self._last_latency_ms = 0.0
            return []
        
        start_time = time.perf_counter()
        
        try:
            entities = await self._call_ner_model(query)
            extractions = self._map_entities_to_metadata(entities, query)
            
            # Filter by confidence threshold
            filtered = [e for e in extractions if e.confidence >= self.confidence_threshold]
            
            if len(filtered) < len(extractions):
                logger.debug(
                    f"Filtered {len(extractions) - len(filtered)} entities "
                    f"below confidence threshold {self.confidence_threshold}"
                )
            
            self._last_latency_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                f"NER extracted {len(filtered)} metadata items from query "
                f"in {self._last_latency_ms:.2f}ms"
            )
            return filtered
            
        except asyncio.TimeoutError:
            self._last_latency_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(
                f"NER extraction timed out after {self._last_latency_ms:.2f}ms "
                f"(limit: {self.timeout_ms}ms)"
            )
            return []
        except aiohttp.ClientError as e:
            self._last_latency_ms = (time.perf_counter() - start_time) * 1000
            if not self._first_failure_logged:
                logger.info(
                    f"NER endpoint unreachable ({self.endpoint}), falling back to regex-only. "
                    f"Check that retriever-ner-ovms container is running. Error: {e}"
                )
                self._first_failure_logged = True
            else:
                logger.debug(f"NER extraction failed with client error: {e}")
            return []
        except Exception as e:
            self._last_latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"NER extraction failed with unexpected error: {e}")
            return []
    
    async def _call_ner_model(self, text: str) -> List[Dict]:
        """Call OVMS NER model using KServe v2 protocol."""

        payload = {
            "inputs": [
                {
                    "name": "input_text",
                    "shape": [1],
                    "datatype": "BYTES",
                    "data": [text]
                }
            ]
        }
        
        timeout = aiohttp.ClientTimeout(total=self.timeout_ms / 1000.0)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self._inference_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise aiohttp.ClientError(
                        f"OVMS returned status {response.status}: {error_text}"
                    )
                
                result = await response.json()
                
                # Parse OVMS response, expected format: {"outputs": [{"name": "entities", "data": [...]}]}
                return self._parse_ovms_response(result)
    
    def _parse_ovms_response(self, response: Dict) -> List[Dict]:
        """Parse OVMS inference response to entity list."""
        entities = []
        
        if 'outputs' not in response:
            logger.warning("OVMS response missing 'outputs' key")
            return entities
        
        for output in response['outputs']:
            if output.get('name') == 'entities' and 'data' in output:
                # Data is list of entity objects or serialized JSON
                data = output['data']
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            entities.append(item)
                        elif isinstance(item, str):
                            try:
                                parsed = json.loads(item)
                                if isinstance(parsed, list):
                                    entities.extend(parsed)
                                elif isinstance(parsed, dict):
                                    entities.append(parsed)
                            except json.JSONDecodeError as e:
                                logger.error("Failed to parse NER entity JSON: %s (raw: %s)", e, item)
        
        return entities
    
    def _map_entities_to_metadata(
        self, 
        entities: List[Dict], 
        query: str
    ) -> List[ExtractedMetadata]:
        """Map NER entities to ExtractedMetadata, merging adjacent same-type entities."""
        extractions = []
        
        for entity in entities:
            # Handle different entity type field names from various NER outputs
            entity_type = entity.get('entity_group',  # HuggingFace aggregation
                          entity.get('entity',        # Standard NER
                          entity.get('label', '')))   # Alternative format
            
            # Remove BIO prefix if present (B-PERSON → PERSON)
            if entity_type.startswith(('B-', 'I-')):
                entity_type = entity_type[2:]
            
            # Check if this entity type maps to a metadata field
            field = ENTITY_FIELD_MAPPING.get(entity_type)
            if field is None:
                continue
            
            # Extract entity details
            word = entity.get('word', entity.get('text', ''))
            score = entity.get('score', entity.get('confidence', 0.5))
            start = entity.get('start', 0)
            end = entity.get('end', len(word))
            
            # Clean up word (remove ## tokenization artifacts)
            word = word.replace('##', '').strip()
            if not word:
                continue
            
            # Determine operator based on entity type
            operator = '==' if entity_type in ('PERSON', 'PER', 'WORK_OF_ART') else 'range'
            
            extraction = ExtractedMetadata(
                field=field,
                value=word,
                operator=operator,
                confidence=float(score),
                source='ner',
                span=(start, end)
            )
            extractions.append(extraction)
            
            logger.debug(
                f"NER entity: type={entity_type}, word='{word}', "
                f"confidence={score:.3f}, field={field}"
            )
        
        # Merge adjacent entities of same type (e.g., "John" + "Smith" → "John Smith")
        extractions = self._merge_adjacent_entities(extractions, query)
        
        return extractions
    
    def _merge_adjacent_entities(
        self, 
        extractions: List[ExtractedMetadata],
        query: str
    ) -> List[ExtractedMetadata]:
        """Merge adjacent entities of same type (e.g., 'John' + 'Smith' → 'John Smith')."""
        if len(extractions) <= 1:
            return extractions
        
        # Sort by span start position
        sorted_extracts = sorted(extractions, key=lambda x: x.span[0])
        
        merged = []
        current = None
        
        for extraction in sorted_extracts:
            if current is None:
                current = extraction
                continue
            
            # Check if should merge with current
            if (
                current.field == extraction.field and
                current.source == extraction.source and
                self._are_adjacent(current.span, extraction.span, query)
            ):
                # Merge: extend value and span
                if isinstance(current.value, str) and isinstance(extraction.value, str):
                    # Get text between spans from original query for accurate merge
                    merged_text = query[current.span[0]:extraction.span[1]]
                    current = ExtractedMetadata(
                        field=current.field,
                        value=merged_text.strip(),
                        operator=current.operator,
                        confidence=min(current.confidence, extraction.confidence),
                        source=current.source,
                        span=(current.span[0], extraction.span[1])
                    )
            else:
                # Not adjacent - save current and start new
                merged.append(current)
                current = extraction
        
        # Do not omit the last one
        if current is not None:
            merged.append(current)
        
        return merged
    
    def _are_adjacent(
        self, 
        span1: Tuple[int, int], 
        span2: Tuple[int, int],
        query: str
    ) -> bool:
        """Check if two spans are adjacent (≤2 chars of whitespace between)."""
        gap_start = span1[1]
        gap_end = span2[0]
        
        if gap_end <= gap_start:
            return True  # Overlapping
        
        gap = query[gap_start:gap_end]
        return len(gap) <= 2 and gap.strip() == ''


class NERExtractorStub(NERExtractor):
    """Stub NER extractor returning empty results. For testing without OVMS."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(endpoint="stub://localhost", model_name="stub")
        logger.info("NERExtractorStub initialized (returns empty results)")
    
    async def extract(self, query: str) -> List[ExtractedMetadata]:
        """Return empty list (stub)."""
        self._last_latency_ms = 0.0
        return []
    
    async def _call_ner_model(self, text: str) -> List[Dict]:
        """No-op: stub never calls a real model."""
        return []
