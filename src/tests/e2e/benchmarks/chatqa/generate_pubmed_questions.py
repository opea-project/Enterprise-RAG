#!/bin/python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import requests
import random
import json
import argparse

def download_pubmed_dataset(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text.splitlines()

def generate_random_questions(lines, n, prefix, suffix):
    if n > len(lines):
        raise ValueError(f"Requested {n} random rows, but file has only {len(lines)} rows.")
    sampled_lines = random.sample(lines, n) # nosec B311
    titles = []
    for line in sampled_lines:
        row = json.loads(line)
        title = row.get('title', '')
        titles.append(f"{prefix} {title} {suffix}")
    return titles

def main():
    parser = argparse.ArgumentParser(description="Helper to download PubMed dataset, sample N random rows, add prefix and suffix, and save to file.")
    parser.add_argument('--url', help='URL to download the JSONL file from', default="https://huggingface.co/datasets/MedRAG/pubmed/resolve/main/chunk/pubmed23n0001.jsonl")
    parser.add_argument('--output', help='Output file to save prefixed titles', default="questions-pubmed.csv")
    parser.add_argument('--rows', type=int, help='Number of random rows to select', default=1024)
    parser.add_argument('--prefix', help='Prefix to add to each title', default="Give me the content related to the following title: ")
    parser.add_argument('--suffix', help='Suffix to add to each title', default="Repeat the answer in loop multiple times, so you return me at least 1000 words.")

    args = parser.parse_args()

    print(f"Downloading file from {args.url} ...")
    lines = download_pubmed_dataset(args.url)
    print(f"Generating {args.rows} random questions and saving to {args.output} ...")
    questions = generate_random_questions(lines, args.rows, args.prefix, args.suffix)
    with open(args.output, 'w', encoding='utf-8') as out:
        for question in questions:
            out.write(question + '\n')
    print("Done.")

if __name__ == '__main__':
    main()
