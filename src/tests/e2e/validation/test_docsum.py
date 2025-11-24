#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest
import requests
import statistics

from validation.buildcfg import cfg

# Skip all tests if docsum pipeline is not deployed
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "docsum":
        break
else:
    pytestmark = pytest.mark.skip(reason="DocSum pipeline is not deployed")

logger = logging.getLogger(__name__)
AVAILABLE_SUMMARY_TYPES = ["stuff", "map_reduce", "refine"]
BAD_REQUEST_STATUS_CODES = [400, 422]


@pytest.mark.smoke
@allure.testcase("IEASG-T289")
def test_docsum_summary_type(docsum_helper, texts):
    """
    Upload a couple of short books - each book using all available summary types.
    Check if the summaries are correct.
    """
    books_to_test = [
        "abdallah_the_unhappy_1k_words",
        "the_god_plllnk_1.3k_words",
        "the_selfish_giant_1.6k_words"
    ]
    failures = []

    for book_title in books_to_test:
        book_text = texts[book_title]
        for summary_type in AVAILABLE_SUMMARY_TYPES:
            logger.info(f"Requesting a summary for a book: {book_title} (summary type: '{summary_type}')")
            response = docsum_helper.call(texts=[book_text], summary_type=summary_type)

            if response.status_code != 200:
                failures.append(f"Unexpected status code "
                                f"(summary type: '{summary_type}', book '{book_title}'): {response.status_code}")
                continue

            failures.extend(docsum_helper.evaluate_summary(response, book_text, book_title, summary_type))
    assert not failures, "\n".join(failures)


@allure.testcase("IEASG-T290")
def test_docsum_long_books(docsum_helper, texts):
    """Upload long books (using map_reduce summary type) and check if the summaries are correct"""
    books_to_test = [
        "yellow_whitepaper_6k_words",
        "the_call_of_the_wild_32k_words",
        "up_from_slavery_an_autobiography_77k_words"
    ]
    failures = []
    for book_title in books_to_test:
        book_text = texts[book_title]
        logger.info(f"Requesting a summary for a book: {book_title}")
        response = docsum_helper.call(texts=[book_text])

        if response.status_code != 200:
            failures.append(f"Unexpected status code "
                            f"(book '{book_title}'): {response.status_code}, response text: {response.text}")
            continue
        failures.extend(docsum_helper.evaluate_summary(response, book_text, book_title))
    assert not failures, "\n".join(failures)


@allure.testcase("IEASG-T291")
def test_docsum_links(docsum_helper):
    """Upload links and check if the summaries are correct"""
    links = [
        "https://www.gutenberg.org/cache/epub/10580/pg10580.txt",
        "https://www.gutenberg.org/cache/epub/14976/pg14976.txt"
    ]
    failures = []
    for link in links:
        logger.info(f"Requesting a summary for a link: {link}")
        response = docsum_helper.call(links=[link])
        if response.status_code != 200:
            failures.append(f"Unexpected status code (link '{link}'): {response.status_code}, response: {response.text}")
            continue
        link_content = requests.get(link).text
        failures.extend(docsum_helper.evaluate_summary(response, link_content, link))
    assert not failures, "\n".join(failures)


@allure.testcase("IEASG-T292")
def test_docsum_files(docsum_helper, texts):
    """Upload files and check if the summaries are correct"""
    files = ["after_a_few_words_3k_words", "the_history_of_the_peloponnesian_war_205k_words"]
    failures = []
    for file in files:
        file_name = f"{file}.txt"
        file_attachment = docsum_helper.prepare_file_attachment(file_name)
        file_content = texts[file]
        logger.info(f"Requesting a summary for a file: {file_name}")
        response = docsum_helper.call(files=[file_attachment])
        if response.status_code != 200:
            failures.append(f"Unexpected status code (file '{file_name}'): {response.status_code}, response: {response.text}")
            continue
        failures.extend(docsum_helper.evaluate_summary(response, file_content, file))
    assert not failures, "\n".join(failures)


@allure.testcase("IEASG-T293")
def test_docsum_confusing_stories(docsum_helper, texts):
    """
    Upload 2 stories - each story consists of random sentences not related to each other.
    Check if the API can handle such input without errors. Do not check the summary quality.
    """
    stories_to_test = [
        "random_sentences_1",
        "random_sentences_2"
    ]
    failures = []
    for story_title in stories_to_test:
        random_sentences = texts[story_title]
        logger.info("Requesting a summary for a confusing story with random sentences.")
        response = docsum_helper.call(texts=[random_sentences])
        if response.status_code != 200:
            failures.append(f"Unexpected status code ({story_title}): {response.status_code}, response: {response.text}")
            continue
        docsum_helper.get_summary(response)
    assert not failures, "\n".join(failures)


@allure.testcase("IEASG-T294")
def test_docsum_multiple_texts(docsum_helper, texts):
    """
    Upload multiple texts in a single request.
    The text that is supposed to be summarized should a concatenation of all uploaded texts.
    Check if the summary is correct.
    """
    text_1 = texts["multiple_texts_1"]
    text_2 = texts["multiple_texts_2"]
    logger.info("Requesting a summary")
    response = docsum_helper.call(texts=[text_1, text_2])
    assert response.status_code == 200,  f"Unexpected status code: {response.status_code}, response: {response.text}"
    failures = docsum_helper.evaluate_summary(response, text_1 + text_2, "Multiple_texts")
    assert not failures, "\n".join(failures)


@allure.testcase("IEASG-T295")
def test_docsum_mixed_parameters(docsum_helper, texts):
    """Upload one text and one file in a single request. Check if the summary is correct."""
    text = texts["multiple_texts_1"]
    file = "multiple_texts_2.txt"
    file_attachment = docsum_helper.prepare_file_attachment(file)
    logger.info("Requesting a summary")
    response = docsum_helper.call(texts=[text], files=[file_attachment])
    assert response.status_code == 200,  f"Unexpected status code: {response.status_code}, response: {response.text}"
    text_from_file = texts["multiple_texts_2"]
    failures = docsum_helper.evaluate_summary(response, text + text_from_file, "Mixed up parameters")
    assert not failures, "\n".join(failures)


@allure.testcase("IEASG-T296")
def test_docsum_streaming(docsum_helper, texts):
    """Request for a summary with streaming enabled and disabled. Check if both summaries are correct."""
    book = "the_gift_of_the_magi_2k_words"
    book_text = texts[book]
    failures = []
    for stream in [True, False]:
        logger.info(f"Requesting a summary for a book: {book} with streaming set to {stream}")
        response = docsum_helper.call(texts=[book_text], stream=stream)
        if response.status_code != 200:
            failures.append(f"Unexpected status code (stream={stream}): {response.status_code}, response text: {response.text}")
            continue
        failures.extend(docsum_helper.evaluate_summary(response, book_text, book))
    assert not failures, "\n".join(failures)


@allure.testcase("IEASG-T297")
def test_docsum_input_over_limit(docsum_helper, texts):
    """ Upload a text exceeding the allowed limit for 'stuff'' summary type. """
    book_title = "the_call_of_the_wild_32k_words"
    logger.info(f"Requesting a summary for a long book: {book_title}")
    response = docsum_helper.call(texts=[texts[book_title]], summary_type="stuff")
    assert response.status_code in BAD_REQUEST_STATUS_CODES


@allure.testcase("IEASG-T298")
def test_docsum_empty_lists(docsum_helper):
    """Test DocSum API with empty lists for texts, links, and files"""
    logger.info("Requesting a summary without providing any text/link/file")
    response = docsum_helper.call(texts=[])
    assert response.status_code in BAD_REQUEST_STATUS_CODES


@allure.testcase("IEASG-T299")
def test_docsum_invalid_request(docsum_helper):
    """
    Test DocSum API with invalid payloads:
    - invalid keys
    - invalid data types
    """
    logger.info("Requesting a summary with an invalid payload")
    response = docsum_helper.call_with_payload(payload={"invalid_key": "invalid_value"})
    assert response.status_code in BAD_REQUEST_STATUS_CODES
    response = docsum_helper.call_with_payload(payload={"texts": "this_should_be_a_list"})
    assert response.status_code in BAD_REQUEST_STATUS_CODES
    response = docsum_helper.call_with_payload(payload={"links": "this_should_be_a_list"})
    assert response.status_code in BAD_REQUEST_STATUS_CODES
    response = docsum_helper.call_with_payload(payload={"files": "this_should_be_a_list"})
    assert response.status_code in BAD_REQUEST_STATUS_CODES
    link = "https://www.gutenberg.org/cache/epub/64982/pg64982.txt"
    response = docsum_helper.call_with_payload(payload={
        "links": [link], "parameters": {"stream": "this_should_be_a_boolean"}})
    assert response.status_code in BAD_REQUEST_STATUS_CODES
    response = docsum_helper.call_with_payload(payload={
        "links": [link], "parameters": {"summary_type": "invalid_summary_type"}})
    assert response.status_code in BAD_REQUEST_STATUS_CODES
    response = docsum_helper.call_with_payload(payload={
        "links": [link], "parameters": {"chunk_size": -100}})
    assert response.status_code in BAD_REQUEST_STATUS_CODES


@allure.testcase("IEASG-T302")
def test_docsum_concurrent_requests(docsum_helper, texts, temporarily_remove_brute_force_detection):
    """
    Make multiple concurrent DocSum API requests.
    Expect all requests to be successful and have correct summaries.
    Measure execution times.
    """
    text = texts["abdallah_the_unhappy_1k_words"]
    concurrent_requests = 10
    execution_times = []
    failed_requests_counter = 0
    similarity_failures = []

    results = docsum_helper.call_in_parallel([text] * concurrent_requests, stream=True)
    for result in results:
        if result.exception is not None:
            logger.info(result.exception)
            failed_requests_counter = + 1
        elif result.status_code != 200:
            logger.info(f"Request failed with status code {result.status_code}. Response body: {result.text}")
            failed_requests_counter += 1
        else:
            execution_times.append(result.response_time)
            similarity_failures.extend(docsum_helper.evaluate_summary(result, text, "abdallah_the_unhappy_1k_words"))

    mean_time = statistics.mean(execution_times)
    max_time = max(execution_times)
    min_time = min(execution_times)

    logger.info(f'Total requests: {concurrent_requests}')
    logger.info(f'Failed requests: {failed_requests_counter}')
    logger.info(f'Mean Execution Time: {mean_time:.4f} seconds')
    logger.info(f'Longest Execution Time: {max_time:.4f} seconds')
    logger.info(f'Shortest Execution Time: {min_time:.4f} seconds')
    assert failed_requests_counter == 0, "Some of the requests didn't return HTTP status code 200"
    assert not similarity_failures, "\n".join(similarity_failures)
