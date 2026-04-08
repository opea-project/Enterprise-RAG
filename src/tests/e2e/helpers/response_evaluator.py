# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Local response quality evaluator for chat UI tests.

Provides rule-based and heuristic evaluation of chatbot responses
without requiring external API calls.
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LocalResponseEvaluator:
    """
    Local response evaluator using rule-based and heuristic methods.

    NO external API calls required - all evaluations are local.
    """

    def __init__(self):
        logger.info("Local response evaluator initialized (no external APIs)")

    def calculate_keyword_relevance(
        self, prompt: str, response: str, expected_keywords: List[str] = None
    ) -> float:
        """Calculate relevance based on keyword overlap."""
        stop_words = {
            "the",
            "is",
            "are",
            "was",
            "were",
            "what",
            "how",
            "why",
            "when",
            "where",
            "which",
            "who",
            "whom",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "from",
            "by",
            "about",
            "as",
            "into",
            "like",
            "through",
            "after",
            "over",
            "between",
            "out",
            "against",
            "during",
            "without",
            "before",
            "under",
            "around",
        }

        prompt_words = set(re.findall(r"\w+", prompt.lower())) - stop_words
        response_words = set(re.findall(r"\w+", response.lower()))

        if not prompt_words:
            return 0.5

        overlap = len(prompt_words & response_words)
        relevance = min(1.0, overlap / len(prompt_words))

        if expected_keywords:
            expected_words = set(kw.lower() for kw in expected_keywords)
            found_keywords = len(expected_words & response_words)
            keyword_bonus = (found_keywords / len(expected_keywords)) * 0.3
            relevance = min(1.0, relevance + keyword_bonus)

        return relevance

    def calculate_completeness(self, response: str, min_length: int = 50) -> float:
        """Calculate response completeness based on length and structure."""
        if not response:
            return 0.0

        length = len(response)
        length_score = min(1.0, length / (min_length * 2))

        sentences = re.split(r"[.!?]+", response)
        sentence_count = len([s for s in sentences if len(s.strip()) > 10])
        structure_score = min(1.0, sentence_count / 3)

        return (length_score * 0.6) + (structure_score * 0.4)

    def calculate_coherence(self, response: str) -> float:
        """Calculate response coherence based on structure and readability."""
        if not response or len(response) < 20:
            return 0.3

        sentences = re.split(r"[.!?]+", response)
        valid_sentences = [s for s in sentences if len(s.strip()) > 5]

        if not valid_sentences:
            return 0.4

        sentence_score = min(1.0, len(valid_sentences) / 4)

        words = re.findall(r"\w+", response.lower())
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            repetition_score = unique_ratio
        else:
            repetition_score = 0.5

        has_structure = bool(re.search(r"(\n-|\n\*|\n\d+\.|\n\u2022)", response))
        structure_bonus = 0.1 if has_structure else 0

        coherence = (sentence_score * 0.5) + (repetition_score * 0.4) + structure_bonus
        return min(1.0, coherence)

    def calculate_groundedness(self, response: str, context: str = None) -> float:
        """Simple groundedness check based on specific claims vs vague statements."""
        if not response:
            return 0.0

        specific_indicators = [
            r"\d+",
            r"(according to|based on|studies show|research indicates)",
            r"(specifically|particularly|namely|for example|such as)",
            r"(first|second|third|finally|additionally)",
        ]

        indicator_count = sum(1 for pattern in specific_indicators if re.search(pattern, response.lower()))
        specificity_score = min(1.0, indicator_count / 3)

        vague_patterns = [
            r"(probably|maybe|might|could be|possibly|perhaps)",
            r"(i think|i believe|in my opinion)",
            r"(generally|usually|often|sometimes)",
        ]

        vague_count = sum(1 for pattern in vague_patterns if re.search(pattern, response.lower()))
        vague_penalty = min(0.4, vague_count * 0.1)

        groundedness = max(0.0, specificity_score - vague_penalty + 0.5)
        return min(1.0, groundedness)

    def calculate_correctness_heuristic(self, prompt: str, response: str) -> float:
        """Heuristic correctness check based on response appropriateness."""
        question_types = {
            "what": ["is", "are", "definition", "concept", "means"],
            "how": ["process", "steps", "method", "way", "procedure"],
            "why": ["because", "reason", "cause", "due to", "since"],
            "when": ["time", "date", "period", "moment", "during"],
            "where": ["location", "place", "position", "at", "in"],
        }

        prompt_lower = prompt.lower()
        response_lower = response.lower()

        question_type = None
        for q_type in question_types:
            if prompt_lower.startswith(q_type):
                question_type = q_type
                break

        if question_type and question_type in question_types:
            indicators = question_types[question_type]
            has_appropriate_answer = any(ind in response_lower for ind in indicators)
            appropriateness_score = 0.8 if has_appropriate_answer else 0.5
        else:
            appropriateness_score = 0.7

        quality_score = self.calculate_completeness(response) * 0.5 + self.calculate_coherence(response) * 0.5

        return (appropriateness_score * 0.6) + (quality_score * 0.4)

    async def evaluate_response(
        self,
        prompt: str,
        response: str,
        context: Optional[str] = None,
        expected_keywords: List[str] = None,
        min_length: int = 50,
    ) -> Dict[str, float]:
        """Evaluate a chat response using local metrics."""
        scores = {}

        try:
            relevance = self.calculate_keyword_relevance(prompt, response, expected_keywords)
            scores["Answer Relevance"] = relevance
            logger.info(f"  Answer Relevance: {relevance:.3f}")

            context_relevance = self.calculate_completeness(response, min_length)
            scores["Context Relevance"] = context_relevance
            logger.info(f"  Context Relevance: {context_relevance:.3f}")

            groundedness = self.calculate_groundedness(response, context)
            scores["Groundedness"] = groundedness
            logger.info(f"  Groundedness: {groundedness:.3f}")

            coherence = self.calculate_coherence(response)
            scores["Coherence"] = coherence
            logger.info(f"  Coherence: {coherence:.3f}")

            correctness = self.calculate_correctness_heuristic(prompt, response)
            scores["Correctness"] = correctness
            logger.info(f"  Correctness: {correctness:.3f}")

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            scores = {
                "Answer Relevance": 0.0,
                "Context Relevance": 0.0,
                "Groundedness": 0.0,
                "Coherence": 0.0,
                "Correctness": 0.0,
            }

        return scores

    def calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted overall quality score."""
        weights = {
            "Answer Relevance": 0.25,
            "Context Relevance": 0.20,
            "Groundedness": 0.25,
            "Coherence": 0.15,
            "Correctness": 0.15,
        }

        return sum(scores.get(metric, 0.0) * weight for metric, weight in weights.items())
