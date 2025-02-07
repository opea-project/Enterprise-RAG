# HTTP Performance Test Benchmark

This Python script is designed to benchmark the performance of HTTP endpoints by sending parallel requests to a specified endpoint and measuring the response times. It helps to assess the responsiveness of RAG services such as prompt template, reranking services, or custom endpoints.

It measures the time taken for each request and provides various performance metrics, including:
 - Min: The minimum response time observed during the test.
 - Max: The maximum response time observed during the test.
 - Avg: The average response time across all requests.
 - Median: The middle value of the response times when sorted.
 - 90th Percentile: The value below which 90% of the response times fall.
 - Variance: The variability in response times; higher variance indicates less consistent performance.

This will help you understand the performance of your service under load, especially when multiple concurrent requests are made.

## Prerequisites
 - Python (3.10+) and **requests** library. You can install it using pip:

    ```bash
    pip install requests
    ```
- The **tested endpoint** should be up and running on your system. Ensure that the endpoint URL is accessible and responds to the provided request body.

## Usage

To get help and see the available options, use the following command:

```bash
python http_perf_test.py --help
```

### Basic Command
```bash
python http_perf_test.py
```

### Customize Test Parameters and Save Results
You can specify the following options:
 - **Parallel Requests** (`-n`): Number of parallel requests to send in each test round (default is 100).
 - **Test Rounds** (`-x`): Number of test rounds to perform (default is 3).
 - **Test Case** (`-t`): Predefined endpoints and request bodies are available for RAG microservices like RERANKING (default) and PROMPT_TEMPLATE. Additionally, you can define your own custom test case in the code under the CUSTOM section. 
 - **Save Results to CSV** (`-o`): Use the -o option followed by a file path to save the benchmark results in a CSV file. If the file does not exist, it will be created with a header. Subsequent runs will append new results as a line below the existing data, preserving all metrics in a single file for analysis.

Example commands:
 - ```python http_perf_test.py -t PROMPT_TEMPLATE -n 100 -x 3```

 - ```python http_perf_test.py -t RERANKING -n 100 -x 3```


 ### Example Output
```
$ python http_perf_test.py -t PROMPT_TEMPLATE -x 3 -n 500 -o results.csv

Endpoint Under Test: http://localhost:7900/v1/prompt_template
Number of parallel requests (N): 500
Number of test rounds (X): 3
Output file: results.csv

Test will start in 3 seconds...

Starting test round 1/3
Round 1 response times: [0.2345, 0.2501, 0.2256, ...]

Starting test round 2/3
Round 2 response times: [0.2457, 0.2483, 0.2334, ...]

Starting test round 3/3
Round 3 response times: [0.2365, 0.2552, 0.2401, ...]

Performance Metrics: (N=500, X=3)
Min: 0.0022 seconds
Max: 0.0958 seconds
Avg: 0.0214 seconds
Median: 0.0187 seconds
90th_percentile: 0.0388 seconds
Variance: 0.0002 seconds

Results saved to results.csv
```

## Defining a Custom Test Case
To define a custom test case, specify the endpoint URL and the request body in the script.
Modify the following part of the script to set your custom values:
```python
elif TEST_CASE == 'CUSTOM':
    ENDPOINT = "http://host:port/endpoint"  # Replace with your custom endpoint
    BODY = {
        # Provide your custom request body here
    }
```
After modifying the script, you can run the benchmark using the CUSTOM test case type
```bash
python http_perf_test.py -t CUSTOM
```

## Possible Error: "Device or Resource is Busy"
If you encounter an error like "device or resource is busy," it typically indicates that the system is overloaded and cannot handle the number of requests being sent in parallel. This can happen if there are too many concurrent requests or if the service under test is not capable of handling such high load.