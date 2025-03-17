# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import boto3
import os
import requests
import time
import json
from dotenv import load_dotenv
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "./.env"))

# Initialize the logger for the microservice
logger = get_opea_logger("edp_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize boto3 client
sqs = boto3.client('sqs')

# URL of the SQS queue
queue_url = os.environ.get('AWS_SQS_EVENT_QUEUE_URL', None)

if queue_url is None:
    logger.exception("AWS_SQS_EVENT_QUEUE_URL is not set")
    raise

# URL of backend
backend_endpoint = os.environ.get('EDP_BACKEND_ENDPOINT', None)

if backend_endpoint is None:
    logger.exception("EDP_BACKEND_ENDPOINT is not set")
    raise

# Poll for messages
while True:
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response.get('Messages', [])
    if messages:
        logger.debug(f"Received {len(messages)} messages from SQS")

        for message in messages:
            logger.debug(f"Received message: {message}")

            data = message['Body']
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise 'Invalid JSON format'

            logger.debug(f"Received message: {data}")

            # Check if records is available
            if data.get('Records', None) is None:
                logger.debug("Records not found in the message")
                # Unqueue this message
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                continue

            logger.debug(f"Sending data to backend: {data}")
            request = requests.post(url=backend_endpoint, json=data)

            if request.ok:
                logger.debug("Request to backend was successful")
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
            else:
                logger.error(f"Request to backend failed: {request.status_code}.")
                logger.error(f"{request.text}")

    time.sleep(1)
