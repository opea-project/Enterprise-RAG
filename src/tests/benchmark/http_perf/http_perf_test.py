# ruff: noqa: E711, E712
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import requests
import concurrent.futures
import statistics
import time
import argparse
import csv
import os

# Configuration
TEST_CASE_CHOICES = ['RERANKING', 'PROMPT_TEMPLATE', 'CUSTOM']

DEFAULT_TEST_CASE = TEST_CASE_CHOICES[0] # Default: RERANKING
DEFAULT_N = 100  # Number of parallel requests
DEFAULT_X = 3   # Number of test rounds


def validate_output_path(path):
    # Resolve the absolute path
    absolute_path = os.path.abspath(path)
    # Define a safe base directory, if applicable
    base_dir = os.getcwd()  # You can specify a different base directory here
    # Ensure the resolved path is within the allowed directory
    if not absolute_path.startswith(base_dir):
        raise argparse.ArgumentTypeError(f"Invalid path: {path}. Path traversal is not allowed.")
    return absolute_path

# Argument parsing
parser = argparse.ArgumentParser(description='HTTP Performance Test')
parser.add_argument('-t', type=str, default=DEFAULT_TEST_CASE, choices=TEST_CASE_CHOICES, help='Service type to test. Default: %(default)s')
parser.add_argument('-n', type=int, default=DEFAULT_N, metavar='REQUESTS', help='Number of parallel requests. Default: %(default)s')
parser.add_argument('-x', type=int, default=DEFAULT_X, metavar='ROUNDS', help='Number of test rounds. Default: %(default)s')
parser.add_argument('-o', type=validate_output_path, metavar='OUTPUT_FILE', help='Path to the output CSV file for saving performance metrics. Default: %(default)s')
args = parser.parse_args()


TEST_CASE = args.t.upper()
N = args.n
X = args.x
OUTPUT_CSV_FILE = args.o

if TEST_CASE == 'PROMPT_TEMPLATE':
    ENDPOINT = "http://localhost:7900/v1/prompt_template"
    PROMPT = "### Please refer to the search results obtained from the local knowledge base. But be careful to not incorporate information that you think is not relevant to the question. If you don't know the answer to a question, please don't share false information. ### Search results: {reranked_docs} \n### Question: {initial_query} \n### Answer:"
    BODY = {
        "prompt_template": PROMPT,
        "data": {
            "initial_query": "What is Deep Learning?",
            "reranked_docs": {
                "text": "Deep Learning is..."
            }
        }
    }
elif TEST_CASE == 'RERANKING':
    ENDPOINT = "http://localhost:8000/v1/reranking"
    BODY = {
        "initial_query": "What is Deep Learning?",
        "retrieved_docs": [{"text": "Deep Learning is not..."}, {"text": "Deep learning is..."}],
        "top_n": 1,
    }

elif TEST_CASE == 'CUSTOM':
    # Define your custom test case by specifying the endpoint and request body.
    ENDPOINT = "http://host:port/endpoint"  # HERE replace with your service's endpoint
    BODY = {
        # HERE Provide the structure of your request body here
    }
else:
    raise ValueError(f"Unsupported test case {TEST_CASE}")


HEADERS = {'Content-Type': 'application/json'}

def send_request():
    """Send a single POST request to the endpoint."""
    start_time = time.perf_counter()
    try:
        response = requests.post(ENDPOINT, json=BODY, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None
    return time.perf_counter() - start_time

def run_test_round():
    """Run one round of N parallel requests and collect response times."""
    response_times = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as executor:
        futures = [executor.submit(send_request) for _ in range(N)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                response_times.append(result)
    return response_times


def calculate_metrics(times):
    """Calculate min, max, avg, median, 90th percentile, and variance."""
    if not times:
        return {}
    metrics = {
        "min": min(times),
        "max": max(times),
        "avg": statistics.mean(times),
        "median": statistics.median(times),
        "90th_percentile": statistics.quantiles(times, n=10)[-1],
        "variance": statistics.variance(times) if len(times) > 1 else 0
    }
    return metrics


def write_metrics_to_csv(timestamp, metrics, filename='metrics.csv'):
    """
    Write the performance metrics to a CSV file, adding a header only if the file is new.
    Args:
        timestamp (str): The timestamp when the metrics were recorded.
        metrics (dict): A dictionary containing performance metrics with keys 'min', 'max', 'avg', 'median', '90th_percentile', and 'variance'.
        filename (str, optional): The name of the CSV file to write to. Defaults to 'metrics.csv'.
    Raises:
        IOError: If there is an issue writing to the file.
    """

    file_exists = os.path.exists(filename)
    csv_header = ['Timestamp', 'SUT', 'Num_Requests', 'Num_Rounds', 'Min', 'Max', 'Avg', 'Median', '90th_Percentile', 'Variance']

    try:
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)

            # Write header only if file does not exist
            if not file_exists:
                writer.writerow(csv_header)

            # Write data
            writer.writerow([timestamp, TEST_CASE, N, X, metrics["min"], metrics["max"], metrics["avg"], metrics["median"], metrics["90th_percentile"], metrics["variance"]])

            print(f"Results saved to: {os.path.abspath(filename)}")
    except IOError as e:
        print(f"Failed to write to file {filename}: {e}")


def print_info():
    print(f"Endpoint Under Test: {ENDPOINT}")
    print(f"Number of parallel requests (N): {N}")
    print(f"Number of test rounds (X): {X}")
    if len(str(BODY)) < 500: # Print the request body only if its length is less than 500 characters
        print(f"Request body: {BODY}")
                                                                  
def main():    
    print_info()
    wait_time = 3
    print(f"\n\nTest will start in {wait_time} seconds...")
    time.sleep(wait_time)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    all_response_times = []
    for i in range(X):
        print(f"Starting test round {i + 1}/{X}")
        round_times = run_test_round()
        all_response_times.extend(round_times)
        print(f"Round {i + 1} response times: {round_times}")

    if all_response_times:
        metrics = calculate_metrics(all_response_times)
        print("\nPerformance Metrics: (N={}, X={})".format(N, X))
        for key, value in metrics.items():
            print(f"{key.capitalize()}: {value:.4f} seconds")

        # Write the metrics to a CSV file
        if OUTPUT_CSV_FILE:
            write_metrics_to_csv(timestamp, metrics, OUTPUT_CSV_FILE)
    else:
        print("No successful responses collected.")

if __name__ == "__main__":
    main()
