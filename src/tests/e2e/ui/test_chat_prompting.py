"""
Copyright (C) 2024-2025 Intel Corporation
SPDX-License-Identifier: Apache-2.0

Test suite for basic chat prompting functionality.

This module contains simple tests for validating:
1. Chat accepts prompts and provides responses
2. Responses are substantial (not empty or errors)
3. Basic keyword presence in responses
4. Conversational context is maintained across messages

These tests focus on functional validation without quality metrics.
"""

import allure
import asyncio
import logging
import pytest

from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

# Skip all tests if chatqa pipeline is not deployed
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "chatqa":
        break
else:
    pytestmark = pytest.mark.skip(reason="ChatQA pipeline is not deployed")


# Test prompts for basic functionality testing
BASIC_TEST_PROMPTS = [
    {
        "prompt": "What is artificial intelligence?",
        "category": "factual",
        "expected_keywords": ["AI", "machine learning", "intelligence", "computer"],
        "min_length": 50,
    },
    {
        "prompt": "What are the benefits of RAG (Retrieval-Augmented Generation) systems in AI?",
        "category": "rag_specific",
        "expected_keywords": ["retrieval", "generation", "context", "knowledge"],
        "min_length": 50,
    },
    {
        "prompt": "Explain machine learning in simple terms.",
        "category": "explanation",
        "expected_keywords": ["machine", "learning", "data", "algorithm"],
        "min_length": 50,
    },
]


# ============================================================================
# TEST CASES
# ============================================================================

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T267")
async def test_single_prompt_response(chat_ui_helper):
    """
    Test that a single prompt receives a valid response.
    
    Success criteria:
    - Prompt is sent successfully
    - Response is received
    - Response is not empty
    - Response meets minimum length requirement
    - Bot message elements have correct data-testid attributes
    """
    test_case = BASIC_TEST_PROMPTS[0]
    prompt = test_case["prompt"]
    
    logger.info(f"Testing single prompt: {prompt}")
    
    page = chat_ui_helper.page
    
    # Send message and get response
    success, response = await chat_ui_helper.send_message(prompt, wait_for_response=True)
    
    # Assert 1: Message sent successfully
    assert success, "Failed to send message"
    logger.info("Assert 1: Message sent successfully")
    
    # Assert 2: Response received
    assert response is not None, "No response received"
    assert len(response) > 0, "Empty response received"
    logger.info(f"Assert 2: Response received ({len(response)} chars)")
    
    # Assert 3: Response meets minimum length
    assert len(response) >= test_case["min_length"], \
        f"Response too short: {len(response)} < {test_case['min_length']}"
    logger.info(f"Assert 3: Response length sufficient: {len(response)} chars")
    
    # Assert 4: Response is not a generic error
    response_lower = response.lower()
    generic_errors = ["error occurred", "something went wrong", "unable to process", "failed to"]
    is_error = any(err in response_lower for err in generic_errors)
    assert not is_error, "Response appears to be an error message"
    logger.info("Assert 4: Response is not a generic error")
    
    # Assert 5: Bot message has correct data-testid attributes
    bot_message = page.locator('[data-testid="bot-message"]').last
    bot_message_visible = await bot_message.is_visible()
    assert bot_message_visible, "Bot message should have data-testid='bot-message'"
    logger.info("Assert 5: Bot message container has correct data-testid")
    
    # Assert 6: Bot message text has correct data-testid
    bot_message_text = page.locator('[data-testid="bot-message__text"]').last
    bot_message_text_visible = await bot_message_text.is_visible()
    assert bot_message_text_visible, "Bot message text should have data-testid='bot-message__text'"
    logger.info("Assert 6: Bot message text has correct data-testid")
    
    logger.info("Test completed: Single prompt validation passed")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T268")
async def test_multiple_prompts_responses(chat_ui_helper):
    """
    Test that multiple prompts all receive valid responses.
    
    Success criteria:
    - All prompts are sent successfully
    - All prompts receive responses
    - All responses are substantial (not empty or too short)
    """
    logger.info(f"Testing {len(BASIC_TEST_PROMPTS)} different prompts")
    
    results = []
    
    for idx, test_case in enumerate(BASIC_TEST_PROMPTS, 1):
        prompt = test_case["prompt"]
        category = test_case["category"]
        
        logger.info(f"\nTest {idx}/{len(BASIC_TEST_PROMPTS)} - Category: {category}")
        logger.info(f"   Prompt: {prompt}")
        
        # Send message
        success, response = await chat_ui_helper.send_message(prompt, wait_for_response=True)
        
        results.append({
            "category": category,
            "success": success,
            "has_response": response is not None and len(response) > 0,
            "response_length": len(response) if response else 0
        })
        
        if success and response:
            logger.info(f"   Response length: {len(response)} chars")
        else:
            logger.error("   Failed to get response")
        
        # Small delay between prompts to avoid overwhelming the UI
        await asyncio.sleep(2)
    
    # Assert 1: All prompts succeeded
    successful_count = sum(1 for r in results if r["success"])
    assert successful_count == len(BASIC_TEST_PROMPTS), \
        f"Only {successful_count}/{len(BASIC_TEST_PROMPTS)} prompts succeeded"
    logger.info(f"Assert 1: All {len(BASIC_TEST_PROMPTS)} prompts sent successfully")
    
    # Assert 2: All prompts received responses
    response_count = sum(1 for r in results if r["has_response"])
    assert response_count == len(BASIC_TEST_PROMPTS), \
        f"Only {response_count}/{len(BASIC_TEST_PROMPTS)} prompts received responses"
    logger.info(f"Assert 2: All {len(BASIC_TEST_PROMPTS)} prompts received responses")
    
    # Assert 3: All responses are substantial
    min_acceptable_length = 30
    substantial_count = sum(1 for r in results if r["response_length"] >= min_acceptable_length)
    assert substantial_count == len(BASIC_TEST_PROMPTS), \
        f"Only {substantial_count}/{len(BASIC_TEST_PROMPTS)} responses were substantial"
    logger.info(f"Assert 3: All responses are substantial (>= {min_acceptable_length} chars)")
    
    logger.info("Test completed: Multiple prompts validation passed")

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T269")
async def test_response_contains_keywords(chat_ui_helper):
    """
    Test that responses contain relevant keywords from the prompt.
    
    Success criteria:
    - Response received
    - Response contains at least some expected keywords
    - Response is not a generic error message
    """
    test_case = BASIC_TEST_PROMPTS[1]  # RAG-specific prompt
    prompt = test_case["prompt"]
    expected_keywords = test_case["expected_keywords"]
    
    logger.info("Testing keyword presence in response")
    logger.info(f"   Prompt: {prompt}")
    logger.info(f"   Expected keywords: {expected_keywords}")
    
    # Send message
    success, response = await chat_ui_helper.send_message(prompt, wait_for_response=True)
    
    # Assert 1: Response received
    assert success and response, "Failed to get response"
    logger.info("Assert 1: Response received")
    
    # Assert 2: Response is substantial
    assert len(response) >= test_case["min_length"], \
        f"Response too short: {len(response)} chars"
    logger.info(f"Assert 2: Response length: {len(response)} chars")
    
    # Log the actual response for debugging
    logger.info(f"Actual response received: {response}")
    
    # Assert 3: Check for keyword presence (at least 1 keyword)
    response_lower = response.lower()
    found_keywords = [kw for kw in expected_keywords if kw.lower() in response_lower]
    assert len(found_keywords) >= 1, \
        f"Expected at least 1 keyword, found {len(found_keywords)}: {found_keywords}. Response was: {response[:200]}"
    logger.info(f"Assert 3: Found keywords: {found_keywords}")
    
    # Assert 4: Response is not a generic error message
    generic_errors = ["error", "sorry", "unable to", "cannot", "failed"]
    has_error_keywords = sum(1 for err in generic_errors if err in response_lower)
    # Allow up to 1 error keyword (might be part of normal response)
    assert has_error_keywords <= 1, "Response appears to be an error message"
    logger.info("Assert 4: Response is not a generic error")
    
    logger.info("Test completed: Keyword validation passed")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T270")
async def test_conversational_context(chat_ui_helper):
    """
    Test that conversational context is maintained across messages.
    
    Success criteria:
    - Multiple messages sent successfully
    - Follow-up questions receive responses
    - Responses suggest contextual understanding
    """
    logger.info("Testing conversational context maintenance")
    
    # First message
    prompt1 = "What is machine learning?"
    logger.info(f"   Message 1: {prompt1}")
    success1, response1 = await chat_ui_helper.send_message(prompt1, wait_for_response=True)
    
    # Assert 1: First response received
    assert success1 and response1, "Failed to get first response"
    assert len(response1) > 30, "First response too short"
    logger.info(f"Assert 1: First response received ({len(response1)} chars)")
    
    await asyncio.sleep(2)
    
    # Follow-up message (relies on context)
    prompt2 = "What are its main applications?"
    logger.info(f"   Message 2: {prompt2}")
    success2, response2 = await chat_ui_helper.send_message(prompt2, wait_for_response=True)
    
    # Assert 2: Follow-up response received
    assert success2 and response2, "Failed to get follow-up response"
    assert len(response2) > 30, "Follow-up response too short"
    logger.info(f"Assert 2: Follow-up response received ({len(response2)} chars)")
    
    # Assert 3: Follow-up response suggests contextual understanding
    # (contains keywords related to machine learning applications)
    response2_lower = response2.lower()
    context_indicators = ["machine learning", "ml", "application", "use", "example"]
    has_context = any(indicator in response2_lower for indicator in context_indicators)
    assert has_context, "Follow-up response may lack contextual understanding"
    logger.info("Assert 3: Follow-up response suggests contextual understanding")
    
    logger.info("Test completed: Conversational context validated")

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T271")
async def test_chat_handles_various_question_types(chat_ui_helper):
    """
    Test that chat handles various types of questions.
    
    Success criteria:
    - Factual questions receive responses
    - Explanation questions receive responses
    - Domain-specific questions receive responses
    """
    question_types = [
        ("factual", "What is artificial intelligence?"),
        ("explanation", "Explain how neural networks work."),
        ("domain", "What is RAG in AI systems?"),
    ]
    
    logger.info("Testing various question types")
    
    results = []
    
    for q_type, prompt in question_types:
        logger.info(f"\n   Testing {q_type} question: {prompt}")
        
        success, response = await chat_ui_helper.send_message(prompt, wait_for_response=True)
        
        results.append({
            "type": q_type,
            "success": success,
            "has_response": response is not None and len(response) > 0
        })
        
        if success and response:
            logger.info(f"      Response received: {len(response)} chars")
        
        await asyncio.sleep(2)
    
    # Assert: All question types received responses
    success_count = sum(1 for r in results if r["success"] and r["has_response"])
    assert success_count == len(question_types), \
        f"Only {success_count}/{len(question_types)} question types got responses"
    logger.info(f"Assert: All {len(question_types)} question types handled successfully")
    
    logger.info("Test completed: Various question types validated")

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T289")
async def test_user_message_display(chat_ui_helper):
    """
    Test that user messages are properly displayed with data-testid attributes.
    
    Steps:
    1. Send a test message
    2. Verify user message wrapper has data-testid="user-message"
    3. Verify user message text has data-testid="user-message__text"
    4. Verify message content matches what was sent
    
    Success criteria:
    - User message container is rendered with correct data-testid
    - User message text is rendered with correct data-testid
    - Message content matches sent message
    """
    logger.info("Testing user message display with data-testid")
    
    test_message = "This is a test message for validation"
    page = chat_ui_helper.page
    
    # Send message (without waiting for response to save time)
    success, _ = await chat_ui_helper.send_message(test_message, wait_for_response=False)
    assert success, "Failed to send message"
    logger.info("Message sent successfully")
    
    # Assert 1: User message container has correct data-testid
    user_message = page.locator('[data-testid="user-message"]').last
    try:
        await user_message.wait_for(state="visible", timeout=5000)
        logger.info("Assert 1: User message container rendered with data-testid='user-message'")
    except Exception as e:
        logger.error(f"User message container not found: {e}")
        pytest.fail("User message container should be rendered with data-testid")
    
    # Assert 2: User message text has correct data-testid
    user_message_text = page.locator('[data-testid="user-message__text"]').last
    try:
        await user_message_text.wait_for(state="visible", timeout=5000)
        logger.info("Assert 2: User message text rendered with data-testid='user-message__text'")
    except Exception as e:
        logger.error(f"User message text not found: {e}")
        pytest.fail("User message text should be rendered with data-testid")
    
    # Assert 3: Message content matches what was sent
    text_content = await user_message_text.text_content()
    assert test_message in text_content, f"Expected '{test_message}' in user message, got '{text_content}'"
    logger.info("Assert 3: User message content matches sent message")
    
    logger.info("Test completed: User message display validated")
