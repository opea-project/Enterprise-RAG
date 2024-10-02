#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import datetime
import json
import logging
import pathlib
import os
import requests
import urllib3


BASE_URL = "https://jira.devtools.intel.com/rest/atm/1.0"
PROJECT_KEY = "IEASG"
ALLURE_DIR = "allure-results"
TEST_CYCLE_PREFIX = "Microservices"
STATUSES_MAPPING = {
    "passed": "Pass",
    "failed": "Fail"
}


class ZephyrConnector:

    def __init__(self, base_url, bearer_token, logger):
        self.base_url = base_url
        self.bearer_token = bearer_token
        self.logger = logger

    def create_test_cycle(self, project_key, cycle_name):
        """Create a test cycle in a given project."""
        url = f"{self.base_url}/testrun"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "projectKey": project_key,
            "name": cycle_name
        }

        try:
            response = requests.post(url, headers=headers, json=payload, verify=False)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create a test cycle: {e}")
            exit(1)
        if response.status_code != requests.codes.CREATED:
            self.logger.error(f"Failed to create a test cycle. Expected 201 status code, "
                              f"got {response.status_code}")
            exit(1)

        test_cycle = response.json()
        logger.debug(f"Test cycle created: {test_cycle}")
        return test_cycle.get("key")

    def update_test_execution_result(self, test_cycle_id, test_case_key, status, comment=""):
        """Update the execution result of a test in a test cycle."""
        url = f"{self.base_url}/testrun/{test_cycle_id}/testcase/{test_case_key}/testresult"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "status": status,
            "comment": comment
        }

        try:
            response = requests.post(url, headers=headers, json=payload, verify=False)
        except requests.exceptions.RequestException as e:
            raise ZephyrApiException(f"Failed to update test result: {e}")
        if response.status_code != requests.codes.CREATED:
            raise ZephyrApiException(f"Failed to update test result. Expected 201 status code, "
                                     f"got {response.status_code}")

        logger.debug(f"Test {test_case_key} result updated")
        response = response.json()
        return response.get("id")

    def upload_attachment_to_test_execution(self, test_result_id, file_path):
        """ Uploads a file as an attachment to a test execution in Zephyr Scale."""
        url = f"{self.base_url}/testresult/{test_result_id}/attachments"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "X-Atlassian-Token": "no-check"
        }
        files = {
            'file': (file_path, open(file_path, 'rb'), 'text/plain')
        }

        try:
            response = requests.post(url, headers=headers, files=files, verify=False)
        except requests.exceptions.RequestException as e:
            raise ZephyrApiException(f"Failed to create attachment: {e}")
        if response.status_code != requests.codes.CREATED:
            raise ZephyrApiException(f"Failed to create attachment. Expected 201 status code, "
                                     f"got {response.status_code}")
        logger.debug("Test attachment created")


class ZephyrApiException(Exception):
    pass


def setup_logging():
    # Disable logs from outer modules
    logging.getLogger("requests").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.basicConfig(level=logging.DEBUG)
    return logging.getLogger("")


def setup_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t", "--token", required=True, help="Jira token")
    parser.add_argument("-c", "--test_cycle", required=False,
                        help="Existing test cycle key. Example: 'IEASG-C204'."
                             "If not set, a new test cycle will be created")
    return parser.parse_args()


def create_test_cycle_name():
    now = datetime.datetime.now()
    return f"{TEST_CYCLE_PREFIX}-{now.strftime('%Y-%m-%d_%H:%M:%S')}"


def browse_allure_reports():
    allure_dir_path = os.path.join(os.getcwd(), ALLURE_DIR)
    return [entry.path for entry in os.scandir(allure_dir_path) if entry.name.endswith("-result.json")]


def get_test_details(report):
    with open(report) as test_result_file_opened:
        test_result = json.loads(test_result_file_opened.read())
        test_name = test_result.get("name")
        jira_links = test_result.get("links", [])
        attachments = test_result.get("attachments", [])
        test_status = STATUSES_MAPPING.get(test_result.get("status"))

        test_issue_key = None
        if jira_links:
            jira_link = jira_links[0].get("url")
            test_issue_key = pathlib.PurePath(jira_link).name

        output_file = None
        if attachments:
            output_file = attachments[0].get("source")

        return test_name, test_status, test_issue_key, output_file


def get_attachment_file_path(attachment_file_name):
    allure_dir_path = os.path.join(os.getcwd(), ALLURE_DIR)
    return os.path.join(allure_dir_path, attachment_file_name)


if __name__ == "__main__":
    logger = setup_logging()
    args = setup_args()
    all_test_succeeded = True

    zc = ZephyrConnector(BASE_URL, args.token, logger)
    if args.test_cycle:
        test_cycle_key = args.test_cycle
    else:
        test_cycle_key = zc.create_test_cycle(PROJECT_KEY, create_test_cycle_name())

    for allure_report in browse_allure_reports():
        name, status, issue_key, attachment = get_test_details(allure_report)

        if not issue_key:
            logger.warning(f"Test '{name}' is not linked to any Zephyr test case. Omitting.")
            continue

        try:
            result_id = zc.update_test_execution_result(test_cycle_key, issue_key, status)
            if attachment:
                attachment_file_path = get_attachment_file_path(attachment)
                zc.upload_attachment_to_test_execution(result_id, attachment_file_path)
            else:
                logger.info(f"Test {name} didn't produce any output. No attachment will be added")
        except ZephyrApiException as e:
            logger.error(e)
            all_test_succeeded = False

    if not all_test_succeeded:
        logger.error("At least one API call to Zephyr failed. Some test results will not be "
                     "reported. See logs for details")
        exit(1)
