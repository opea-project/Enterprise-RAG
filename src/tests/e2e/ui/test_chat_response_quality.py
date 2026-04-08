"""
Copyright (C) 2024-2026 Intel Corporation
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
import statistics
import time

import pytest

from tests.e2e.helpers.response_evaluator import LocalResponseEvaluator
from tests.e2e.ui.conftest import requires_chatqa

logger = logging.getLogger(__name__)

pytestmark = requires_chatqa


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
