#!/bin/python3
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import csv
import json
import logging
import os
import signal
import sys
import threading
import time
import linecache
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from queue import Empty, Queue
import requests
from transformers import AutoTokenizer

class QueryPool:
    def __init__(self, file_path=None):
        self.lock = threading.Lock()
        self.next = 0
        self.questions = []
        if file_path:
            with open(file_path, "r") as f:
                self.questions = [line.strip() for line in f if line.strip()]
        else:
            self.questions = ["What is the total revenue of Intel in 2023?"]

    def get(self):
        with self.lock:
            question = self.questions[self.next % len(self.questions)]
            self.next += 1
            return question

class Result:
    def __init__(self):
        self.question_len = 0
        self.answer_len = 0
        self.first_chunk = 0
        self.overall = 0
        self.err = None
        self.code = 0

def parse_args():
    parser = argparse.ArgumentParser(description="Load testing tool.")
    parser.add_argument("-f", type=str, help="Question File Location")
    parser.add_argument("-s", type=str, default="https://erag.com/api/v1/chatqna", help="Server Address format")
    parser.add_argument("-c", type=int, default=32, help="Concurrency Number")
    parser.add_argument("-d", type=str, default="30m", help="Execute Duration, when to stop the test")
    parser.add_argument("-u", type=str, default="0s", help="Worker startup delay time")
    parser.add_argument("-m", type=str, default="BAAI/bge-base-en-v1.5", help="tokenizer model")
    parser.add_argument("-e", type=int, default=200, help="Failures allowed before quitting")
    parser.add_argument("-b", type=str, default="uat.txt", help="Path to file with UAT")
    return parser.parse_args()

def duration_to_seconds(duration_str):
    units = {"s": 1, "m": 60, "h": 3600}
    return float(duration_str[:-1]) * units[duration_str[-1]]

def collect_results(stop_event, result_queue, output_file):
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        while not stop_event.is_set() or not result_queue.empty():
            try:
                res = result_queue.get(timeout=0.1)
                writer.writerow([res.question_len, res.answer_len, res.first_chunk, res.overall, res.err, res.code])
                csvfile.flush()
            except Empty:
                continue

def worker(wid, ctx, server, pool, result_queue, delay, tokenizer, bearer_file):
    time.sleep(delay)
    iteration = 0
    bearer = linecache.getline(bearer_file, (wid + 1)).replace('\n','')
    logging.info(f"[{wid}] worker started with {delay} delay")
    if not bearer:
        logging.error(f"[{wid}] no bearer, quitting")
        return

    while not ctx.is_set():
        question = pool.get()
        res = call_chatqa(server, question, wid, tokenizer, bearer)
        if iteration > 0 and res.answer_len != 1 and res.code == 200 and not res.err:
            result_queue.put(res)
        iteration = iteration + 1
        if ctx.is_set():
            break

def call_chatqa(url, question, wid, tokenizer, bearer):

    headers = {"Content-Type": "application/json", "authorization": "Bearer " + bearer}
    data = json.dumps({"text": question})

    res = Result()
    input_tokens = tokenizer.encode(question)
    res.question_len = len(input_tokens)

    start = time.time()
    try:
        response = requests.post(url, headers=headers, data=data, stream=True,
                                 verify="/etc/ssl/certs/ca-certificates.crt")
        res.code = response.status_code
        answer = ""
        lines = ""
        if response.status_code == 200:
            reader = response.iter_lines()
            for line in reader:
                lines = lines + line.decode("unicode_escape")
                if line == b"data: [DONE]":
                    break
                if line.startswith(b"data: "):
                    line = line[7:-1].decode("unicode_escape")
                    answer = answer + line
                    if res.first_chunk == 0:
                        res.first_chunk = time.time() - start
                    logging.debug(f"[{wid}] A: {line}")
            res.overall = time.time() - start
            output_tokens = tokenizer.encode(answer)
            res.answer_len = len(output_tokens)
            if res.answer_len == 1:
                logging.error(f"[{wid}] unexpected output {lines}")
                os.kill(os.getpid(), signal.SIGUSR1)
        elif response.status_code == 429:
            logging.error(f"[{wid}] hitting ratelimiter, sleeping for 5 seconds")
            time.sleep(5)
        else:
            totaltime = time.time() - start
            logging.error(f"[{wid}] unexpected response code {response.status_code} after {totaltime}")
            os.kill(os.getpid(), signal.SIGUSR1)
    except Exception as e:
        res.err = str(e)
        logging.error(f"[{wid}] exception {e}")
        os.kill(os.getpid(), signal.SIGUSR1)

    return res

def signal_handler(var, signal, frame):
    var[0] = var[0] + 1

def main():
    args = parse_args()
    print(' \n'.join(f'{k}: {v}' for k, v in vars(args).items()))

    tokenizer = AutoTokenizer.from_pretrained(args.m)

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    stop_event = threading.Event()
    signal.signal(signal.SIGINT, lambda s, f: stop_event.set())

    pool = QueryPool(args.f)
    num_workers = args.c
    duration = duration_to_seconds(args.d)
    delay_unit = duration_to_seconds(args.u)
    output_file = f"./bench_{time.strftime('%m%d-%H%M')}_c-{num_workers}_d-{args.u}.result.csv"
    result_queue = Queue()

    failures_allowed = args.e
    failed_count = [0]
    error = 0
    signal.signal(signal.SIGUSR1, partial(signal_handler, failed_count))

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        collector_thread = threading.Thread(target=collect_results, args=(stop_event, result_queue, output_file))
        collector_thread.start()

        start_time = time.time()
        futures = []
        for i in range(num_workers):
            delay = i * delay_unit
            futures.append(
                executor.submit(
                    worker, i, stop_event, args.s, pool, result_queue, delay, tokenizer, args.b
                )
            )

        while time.time() - start_time < duration and not stop_event.is_set():
            time.sleep(1)
            if failed_count[0] > failures_allowed:
                print(f"allowed failures {failed_count[0]} exceeded, quitting")
                executor.shutdown(wait=False, cancel_futures=True)
                error = 1
                break

        stop_event.set()
        for future in futures:
            future.result()

        collector_thread.join()
        sys.exit(error)

if __name__ == "__main__":
    main()
