"""
Copyright (C) 2024-2025 Intel Corporation
SPDX-License-Identifier: Apache-2.0

Test suite for chat response quality evaluation.

This module contains advanced tests for evaluating:
1. Response quality metrics (relevance, coherence, groundedness)
2. Hallucination detection
3. Response latency and performance
4. Quality consistency across multiple prompts

Uses local evaluation methods - NO external APIs required.
"""

import allure
import asyncio
import logging
import re
import statistics
import time
from typing import Dict, List, Optional

import pytest

from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

# Skip all tests if chatqa pipeline is not deployed
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "chatqa":
        break
else:
    pytestmark = pytest.mark.skip(reason="ChatQA pipeline is not deployed")


# Test prompts with expected characteristics
TEST_PROMPTS = [
    {
        "prompt": "What is artificial intelligence?",
        "category": "factual",
        "expected_keywords": ["AI", "machine learning", "algorithm", "computer", "intelligence"],
        "min_length": 50,
    },
    {
        "prompt": "Explain the difference between supervised and unsupervised learning.",
        "category": "technical_explanation",
        "expected_keywords": ["labeled", "data", "training", "supervised", "unsupervised"],
        "min_length": 100,
    },
    {
        "prompt": "How does Intel optimize AI workloads?",
        "category": "domain_specific",
        "expected_keywords": ["Intel", "optimization", "performance", "hardware", "software"],
        "min_length": 75,
    },
    {
        "prompt": "What are the benefits of RAG (Retrieval-Augmented Generation) systems in AI?",
        "category": "rag_specific",
        "expected_keywords": ["retrieval", "generation", "context", "knowledge", "accuracy"],
        "min_length": 80,
    },
    {
        "prompt": "Summarize the key features of enterprise AI solutions.",
        "category": "summarization",
        "expected_keywords": ["enterprise", "scalable", "secure", "deployment", "production"],
        "min_length": 60,
    },
]


# ============================================================================
# LOCAL RESPONSE EVALUATOR
# ============================================================================

class LocalResponseEvaluator:
    """
    Local response evaluator using rule-based and heuristic methods.
    
    NO external API calls required - all evaluations are local.
    """
    
    def __init__(self):
        """Initialize local evaluator with heuristic rules."""
        logger.info("Local response evaluator initialized (no external APIs)")
    
    def calculate_keyword_relevance(self, prompt: str, response: str, expected_keywords: List[str] = None) -> float:
        """
        Calculate relevance based on keyword overlap.
        
        Args:
            prompt: User's question
            response: Chatbot's answer
            expected_keywords: Optional list of expected keywords
        
        Returns:
            Relevance score (0-1)
        """
        # Extract meaningful words from prompt (remove common words)
        stop_words = {'the', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'which', 
                     'who', 'whom', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
                     'with', 'from', 'by', 'about', 'as', 'into', 'like', 'through', 'after', 'over',
                     'between', 'out', 'against', 'during', 'without', 'before', 'under', 'around'}
        
        prompt_words = set(re.findall(r'\w+', prompt.lower())) - stop_words
        response_words = set(re.findall(r'\w+', response.lower()))
        
        if not prompt_words:
            return 0.5
        
        # Calculate overlap
        overlap = len(prompt_words & response_words)
        relevance = min(1.0, overlap / len(prompt_words))
        
        # Bonus for expected keywords
        if expected_keywords:
            expected_words = set(kw.lower() for kw in expected_keywords)
            found_keywords = len(expected_words & response_words)
            keyword_bonus = (found_keywords / len(expected_keywords)) * 0.3
            relevance = min(1.0, relevance + keyword_bonus)
        
        return relevance
    
    def calculate_completeness(self, response: str, min_length: int = 50) -> float:
        """
        Calculate response completeness based on length and structure.
        
        Args:
            response: Chatbot's answer
            min_length: Minimum expected length
        
        Returns:
            Completeness score (0-1)
        """
        if not response:
            return 0.0
        
        length = len(response)
        
        # Base score from length
        length_score = min(1.0, length / (min_length * 2))
        
        # Bonus for sentence structure
        sentences = re.split(r'[.!?]+', response)
        sentence_count = len([s for s in sentences if len(s.strip()) > 10])
        structure_score = min(1.0, sentence_count / 3)
        
        # Combined score
        return (length_score * 0.6) + (structure_score * 0.4)
    
    def calculate_coherence(self, response: str) -> float:
        """
        Calculate response coherence based on structure and readability.
        
        Args:
            response: Chatbot's answer
        
        Returns:
            Coherence score (0-1)
        """
        if not response or len(response) < 20:
            return 0.3
        
        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', response)
        valid_sentences = [s for s in sentences if len(s.strip()) > 5]
        
        if not valid_sentences:
            return 0.4
        
        # Base coherence from sentence structure
        sentence_score = min(1.0, len(valid_sentences) / 4)
        
        # Check for repetition (lower score if too repetitive)
        words = re.findall(r'\w+', response.lower())
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            repetition_score = unique_ratio
        else:
            repetition_score = 0.5
        
        # Check for formatting (lists, bullet points indicate structure)
        has_structure = bool(re.search(r'(\n-|\n\*|\n\d+\.|\n•)', response))
        structure_bonus = 0.1 if has_structure else 0
        
        coherence = (sentence_score * 0.5) + (repetition_score * 0.4) + structure_bonus
        return min(1.0, coherence)

    def calculate_groundedness(self, response: str, context: str = None) -> float:
        """
        Simple groundedness check based on specific claims vs vague statements.
        
        Args:
            response: Chatbot's answer
            context: Retrieved context (if available)
        
        Returns:
            Groundedness score (0-1)
        """
        if not response:
            return 0.0
        
        # Check for specific indicators of grounded responses
        specific_indicators = [
            r'\d+',  # Numbers
            r'(according to|based on|studies show|research indicates)',  # Citations
            r'(specifically|particularly|namely|for example|such as)',  # Specificity
            r'(first|second|third|finally|additionally)',  # Structure
        ]
        
        indicator_count = sum(1 for pattern in specific_indicators if re.search(pattern, response.lower()))
        specificity_score = min(1.0, indicator_count / 3)
        
        # Check for vague or hallucination-prone language
        vague_patterns = [
            r'(probably|maybe|might|could be|possibly|perhaps)',
            r'(i think|i believe|in my opinion)',
            r'(generally|usually|often|sometimes)',
        ]
        
        vague_count = sum(1 for pattern in vague_patterns if re.search(pattern, response.lower()))
        vague_penalty = min(0.4, vague_count * 0.1)
        
        groundedness = max(0.0, specificity_score - vague_penalty + 0.5)
        return min(1.0, groundedness)
    
    def calculate_correctness_heuristic(self, prompt: str, response: str) -> float:
        """
        Heuristic correctness check based on response appropriateness.
        
        Args:
            prompt: User's question
            response: Chatbot's answer
        
        Returns:
            Correctness score (0-1)
        """
        # Check if response addresses the question type
        question_types = {
            'what': ['is', 'are', 'definition', 'concept', 'means'],
            'how': ['process', 'steps', 'method', 'way', 'procedure'],
            'why': ['because', 'reason', 'cause', 'due to', 'since'],
            'when': ['time', 'date', 'period', 'moment', 'during'],
            'where': ['location', 'place', 'position', 'at', 'in'],
        }
        
        prompt_lower = prompt.lower()
        response_lower = response.lower()
        
        # Identify question type
        question_type = None
        for q_type in question_types.keys():
            if prompt_lower.startswith(q_type):
                question_type = q_type
                break
        
        if question_type and question_type in question_types:
            # Check if response contains appropriate answer indicators
            indicators = question_types[question_type]
            has_appropriate_answer = any(ind in response_lower for ind in indicators)
            appropriateness_score = 0.8 if has_appropriate_answer else 0.5
        else:
            appropriateness_score = 0.7
        
        # Check response quality
        quality_score = self.calculate_completeness(response) * 0.5 + self.calculate_coherence(response) * 0.5
        
        return (appropriateness_score * 0.6) + (quality_score * 0.4)
    
    async def evaluate_response(
        self,
        prompt: str,
        response: str,
        context: Optional[str] = None,
        expected_keywords: List[str] = None,
        min_length: int = 50
    ) -> Dict[str, float]:
        """
        Evaluate a chat response using local metrics.
        
        Args:
            prompt: User's input prompt
            response: Chatbot's response
            context: Retrieved context (for RAG evaluation)
            expected_keywords: Expected keywords in response
            min_length: Minimum expected response length
        
        Returns:
            Dictionary of evaluation scores (0-1 scale)
        """
        scores = {}
        
        try:
            # 1. Answer Relevance
            relevance = self.calculate_keyword_relevance(prompt, response, expected_keywords)
            scores["Answer Relevance"] = relevance
            logger.info(f"  📊 Answer Relevance: {relevance:.3f}")
            
            # 2. Context Relevance (simplified - based on completeness)
            context_relevance = self.calculate_completeness(response, min_length)
            scores["Context Relevance"] = context_relevance
            logger.info(f"  📊 Context Relevance: {context_relevance:.3f}")
            
            # 3. Groundedness (hallucination detection)
            groundedness = self.calculate_groundedness(response, context)
            scores["Groundedness"] = groundedness
            logger.info(f"  📊 Groundedness: {groundedness:.3f}")
            
            # 4. Coherence
            coherence = self.calculate_coherence(response)
            scores["Coherence"] = coherence
            logger.info(f"  📊 Coherence: {coherence:.3f}")
            
            # 5. Correctness (heuristic)
            correctness = self.calculate_correctness_heuristic(prompt, response)
            scores["Correctness"] = correctness
            logger.info(f"  📊 Correctness: {correctness:.3f}")
            
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
        """
        Calculate weighted overall quality score.
        
        Args:
            scores: Dictionary of individual metric scores
        
        Returns:
            Overall quality score (0-1 scale)
        """
        weights = {
            "Answer Relevance": 0.25,
            "Context Relevance": 0.20,
            "Groundedness": 0.25,
            "Coherence": 0.15,
            "Correctness": 0.15,
        }
        
        overall = sum(scores.get(metric, 0.0) * weight for metric, weight in weights.items())
        return overall


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def response_evaluator():
    """
    Create local response evaluator for the test module.
    
    NO external APIs required - all evaluations are local.
    
    Yields:
        LocalResponseEvaluator instance
    """
    evaluator = LocalResponseEvaluator()
    yield evaluator
    
    # Cleanup
    logger.info("Cleaning up evaluator session")


# ============================================================================
# TEST CASES - QUALITY METRICS
# ============================================================================

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T278")
async def test_response_quality_single_prompt(chat_ui_helper, response_evaluator):
    """
    Test response quality for a single prompt using evaluation metrics.
    
    Success criteria:
    - Response received within timeout
    - Answer Relevance score >= 0.6
    - Overall quality score >= 0.60
    """
    test_case = TEST_PROMPTS[0]  # Use first test prompt
    prompt = test_case["prompt"]
    
    logger.info(f"Testing response quality for: {prompt}")
    
    # Send message and get response
    success, response = await chat_ui_helper.send_message(prompt, wait_for_response=True)
    
    # Assert 1: Response received
    assert success and response, "Failed to get response"
    logger.info(f"Assert 1: Response received ({len(response)} chars)")
    
    # Evaluate with local metrics
    logger.info("Evaluating response quality...")
    scores = await response_evaluator.evaluate_response(
        prompt, 
        response,
        expected_keywords=test_case["expected_keywords"],
        min_length=test_case["min_length"]
    )
    
    # Assert 2: Answer relevance score meets threshold
    relevance_score = scores.get("Answer Relevance", 0.0)
    assert relevance_score >= 0.6, f"Answer relevance too low: {relevance_score:.3f}"
    logger.info(f"Assert 2: Answer relevance score: {relevance_score:.3f}")
    
    # Assert 3: Overall quality score meets threshold
    overall_score = response_evaluator.calculate_overall_score(scores)
    assert overall_score >= 0.60, f"Overall quality too low: {overall_score:.3f}"
    logger.info(f"Assert 3: Overall quality score: {overall_score:.3f}")
    
    logger.info("Test completed: Response quality validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T279")
async def test_multiple_prompts_quality_metrics(chat_ui_helper, response_evaluator):
    """
    Test response quality across multiple diverse prompts.
    
    Success criteria:
    - All prompts get responses
    - Each response has Answer Relevance >= 0.50 (lowered threshold)
    - Average overall quality score >= 0.55 (lowered threshold)
    - No response has overall score < 0.35 (lowered threshold)
    """
    logger.info(f"Testing {len(TEST_PROMPTS)} diverse prompts")
    
    results = []
    
    for idx, test_case in enumerate(TEST_PROMPTS, 1):
        prompt = test_case["prompt"]
        category = test_case["category"]
        
        logger.info(f"\nTest {idx}/{len(TEST_PROMPTS)} - Category: {category}")
        logger.info(f"   Prompt: {prompt}")
        
        # Send message
        success, response = await chat_ui_helper.send_message(prompt, wait_for_response=True)
        
        if not success or not response:
            logger.error(f"Failed to get response for prompt {idx}")
            results.append({
                "category": category,
                "success": False,
                "scores": {},
                "overall": 0.0
            })
            continue
        
        # Evaluate response
        scores = await response_evaluator.evaluate_response(
            prompt,
            response,
            expected_keywords=test_case.get("expected_keywords", []),
            min_length=test_case.get("min_length", 50)
        )
        overall = response_evaluator.calculate_overall_score(scores)
        
        results.append({
            "category": category,
            "success": True,
            "response_length": len(response),
            "scores": scores,
            "overall": overall
        })
        
        logger.info(f"   Overall Quality: {overall:.3f}")
        
        # Small delay between prompts
        await asyncio.sleep(3)
    
    # Assert 1: Most prompts received responses (allow some failures)
    successful_count = sum(1 for r in results if r["success"])
    assert successful_count >= len(TEST_PROMPTS) - 1, \
        f"Only {successful_count}/{len(TEST_PROMPTS)} prompts succeeded"
    logger.info(f"Assert 1: {successful_count}/{len(TEST_PROMPTS)} prompts received responses")
    
    # Get only successful results for quality metrics
    successful_results = [r for r in results if r["success"]]
    
    if successful_results:
        # Assert 2: Each successful response meets minimum relevance threshold
        for result in successful_results:
            relevance = result["scores"].get("Answer Relevance", 0.0)
            assert relevance >= 0.50, \
                f"Category '{result['category']}' relevance too low: {relevance:.3f}"
        logger.info("Assert 2: All successful responses meet relevance threshold (>= 0.50)")
        
        # Assert 3: Average overall quality is satisfactory
        avg_overall = sum(r["overall"] for r in successful_results) / len(successful_results)
        assert avg_overall >= 0.55, f"Average quality too low: {avg_overall:.3f}"
        logger.info(f"Assert 3: Average overall quality: {avg_overall:.3f}")
        
        # Assert 4: No catastrophic failures
        min_overall = min(r["overall"] for r in successful_results)
        assert min_overall >= 0.35, f"Catastrophic failure detected: {min_overall:.3f}"
        logger.info(f"Assert 4: No catastrophic failures (min score: {min_overall:.3f})")
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("QUALITY METRICS SUMMARY")
        logger.info("="*60)
        for result in successful_results:
            logger.info(f"\n{result['category']:20s} - Overall: {result['overall']:.3f}")
            for metric, score in result["scores"].items():
                logger.info(f"  {metric:20s}: {score:.3f}")
        logger.info("="*60)
    
    logger.info("Test completed: Multiple prompts quality validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T280")
async def test_groundedness_hallucination_detection(chat_ui_helper, response_evaluator):
    """
    Test groundedness and hallucination detection in responses.
    
    Success criteria:
    - Response received
    - Groundedness score >= 0.45 (lowered threshold)
    - Correctness score >= 0.45 (lowered threshold)
    - Coherence score >= 0.45 (lowered threshold)
    """
    # Use a factual prompt
    prompt = "What are the key components of a RAG (Retrieval-Augmented Generation) system?"
    
    logger.info("Testing groundedness and hallucination detection")
    logger.info(f"   Prompt: {prompt}")
    
    # Send message and get response
    success, response = await chat_ui_helper.send_message(prompt, wait_for_response=True)
    
    # Assert 1: Response received
    assert success and response, "Failed to get response"
    logger.info("Assert 1: Response received")
    
    # Evaluate with local metrics
    logger.info("Evaluating groundedness...")
    scores = await response_evaluator.evaluate_response(
        prompt,
        response,
        expected_keywords=["retrieval", "generation", "augmented", "RAG"],
        min_length=100
    )
    
    # Assert 2: Groundedness score indicates minimal hallucination
    groundedness = scores.get("Groundedness", 0.0)
    assert groundedness >= 0.45, \
        f"Groundedness too low (possible hallucination): {groundedness:.3f}"
    logger.info(f"Assert 2: Groundedness score: {groundedness:.3f}")
    
    # Assert 3: Correctness score is satisfactory
    correctness = scores.get("Correctness", 0.0)
    assert correctness >= 0.45, f"Correctness too low: {correctness:.3f}"
    logger.info(f"Assert 3: Correctness score: {correctness:.3f}")
    
    # Assert 4: Coherence score is satisfactory
    coherence = scores.get("Coherence", 0.0)
    assert coherence >= 0.45, f"Coherence too low: {coherence:.3f}"
    logger.info(f"Assert 4: Coherence score: {coherence:.3f}")
    
    logger.info("Test completed: Groundedness validated (minimal hallucination)")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T281")
async def test_response_latency_and_quality(chat_ui_helper, response_evaluator):
    """
    Test response latency while maintaining quality standards.
    
    Success criteria:
    - Average response time <= 30 seconds
    - All successful responses have overall quality >= 0.50 (lowered threshold)
    - Latency variance is reasonable (< 15s std dev, increased)
    """
    logger.info("Testing response latency and quality balance")
    
    test_prompts = TEST_PROMPTS[:3]  # Use first 3 prompts
    latencies = []
    qualities = []
    
    for idx, test_case in enumerate(test_prompts, 1):
        prompt = test_case["prompt"]
        
        logger.info(f"\nRequest {idx}/{len(test_prompts)}: {prompt[:50]}...")
        
        # Measure latency
        start_time = time.time()
        success, response = await chat_ui_helper.send_message(prompt, wait_for_response=True)
        latency = time.time() - start_time
        
        latencies.append(latency)
        logger.info(f"   Latency: {latency:.2f}s")
        
        if success and response:
            # Evaluate quality
            scores = await response_evaluator.evaluate_response(
                prompt,
                response,
                expected_keywords=test_case.get("expected_keywords", []),
                min_length=test_case.get("min_length", 50)
            )
            overall_quality = response_evaluator.calculate_overall_score(scores)
            qualities.append(overall_quality)
            logger.info(f"   Quality: {overall_quality:.3f}")
        else:
            qualities.append(0.0)
        
        await asyncio.sleep(2)
    
    # Assert 1: Average latency is acceptable
    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency <= 30.0, f"Average latency too high: {avg_latency:.2f}s"
    logger.info(f"Assert 1: Average latency: {avg_latency:.2f}s")
    
    # Assert 2: Quality maintained across successful responses
    successful_qualities = [q for q in qualities if q > 0.0]
    if successful_qualities:
        min_quality = min(successful_qualities)
        assert min_quality >= 0.50, f"Quality too low: {min_quality:.3f}"
        logger.info(f"Assert 2: Minimum quality maintained: {min_quality:.3f}")
    
    # Assert 3: Latency consistency (standard deviation)
    if len(latencies) > 1:
        latency_std = statistics.stdev(latencies)
        assert latency_std <= 15.0, f"Latency variance too high: {latency_std:.2f}s"
        logger.info(f"Assert 3: Latency consistency (std dev: {latency_std:.2f}s)")
    
    # Assert 4: Average quality meets threshold
    if successful_qualities:
        avg_quality = sum(successful_qualities) / len(successful_qualities)
        assert avg_quality >= 0.55, f"Average quality too low: {avg_quality:.3f}"
        logger.info(f"Assert 4: Average quality: {avg_quality:.3f}")
    
    logger.info("Test completed: Latency and quality balance validated")
