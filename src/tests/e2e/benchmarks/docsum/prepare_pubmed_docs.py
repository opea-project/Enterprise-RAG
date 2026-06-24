#!/usr/bin/env python3
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Download pubmed JSONL and generate target-size test documents for DocSum benchmark."""

import csv
import json
import os
import subprocess  # nosec B404 - invoked with a fixed argument list only; URL is validated to match https scheme before use
import sys
import urllib.parse
import urllib.request
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DOCS_DIR = SCRIPT_DIR / "docs"
DOCUMENTS_CSV = SCRIPT_DIR / "documents.csv"

TARGET_DOCS = {
    "pubmed_3k.txt": 3000,
    "pubmed_67k.txt": 67000,
    "pubmed_139k.txt": 139000,
}


def download_pubmed():
    """Download pubmed JSONL from URL in documents.csv if not already present."""
    with open(DOCUMENTS_CSV) as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            if len(row) >= 2 and row[1].strip() == "pubmed.jsonl":
                url = row[0].strip()
                break
        else:
            print("Error: pubmed.jsonl URL not found in documents.csv", file=sys.stderr)
            sys.exit(1)

    if urllib.parse.urlparse(url).scheme != "https":
        print(f"Error: URL scheme expected to be https, got: {url[:80]}", file=sys.stderr)
        sys.exit(1)

    dest = DOCS_DIR / "pubmed.jsonl"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"  pubmed.jsonl already present ({dest.stat().st_size // 1_000_000}MB)")
        return dest

    print(f"  Downloading pubmed.jsonl from {url[:80]}...")
    os.makedirs(DOCS_DIR, exist_ok=True)

    try:
        subprocess.run(
            ["curl", "-fSL", "--max-time", "300", "-o", str(dest), url],
            check=True, timeout=320,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"  curl failed ({e}), falling back to urllib...", file=sys.stderr)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as out:  # nosec B310 - scheme validated to match https
            total = 0
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                total += len(chunk)
                print(f"\r  Downloaded {total // 1_000_000}MB", end="", flush=True)
        print()
    return dest


def load_tokenizer():
    """Load tokenizer for accurate token counting, fallback to word approximation."""
    model = os.environ.get("BENCHMARK_TOKENIZER", "casperhansen/llama-3.2-3b-instruct-awq")
    try:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(model, token=os.environ.get("HF_TOKEN"))
        print(f"  Using tokenizer: {model}")
        return tok
    except Exception as e:
        print(f"  Tokenizer unavailable ({e}), using word-count approximation")
        return None


def count_tokens(text, tokenizer):
    if tokenizer is not None:
        return len(tokenizer.encode(text))
    return int(len(text.split()) * 1.3)


def extract_articles(jsonl_path):
    """Extract article texts from pubmed JSONL."""
    articles = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = obj.get("content") or obj.get("contents") or obj.get("text") or obj.get("abstract", "")
            title = obj.get("title", "")
            if text:
                full = f"{title}\n\n{text}\n\n" if title else f"{text}\n\n"
                articles.append(full)
    return articles


def generate_doc(articles, target_tokens, tokenizer, output_path):
    """Concatenate articles until target token count is reached."""
    if output_path.exists():
        existing_text = output_path.read_text(encoding="utf-8")
        existing_tokens = count_tokens(existing_text, tokenizer)
        if abs(existing_tokens - target_tokens) < target_tokens * 0.05:
            print(f"  {output_path.name} already exists ({existing_tokens} tokens)")
            return

    parts = []
    current_tokens = 0
    for article in articles:
        article_tokens = count_tokens(article, tokenizer)
        if current_tokens + article_tokens > target_tokens * 1.02:
            break
        parts.append(article)
        current_tokens += article_tokens

    text = "".join(parts)
    actual_tokens = count_tokens(text, tokenizer)
    output_path.write_text(text, encoding="utf-8")
    print(f"  Generated {output_path.name}: {actual_tokens} tokens ({len(parts)} articles)")


def main():
    print("=== Preparing DocSum benchmark documents ===")
    print()

    os.makedirs(DOCS_DIR, exist_ok=True)

    all_exist = all((DOCS_DIR / name).exists() for name in TARGET_DOCS)
    if all_exist:
        print("All target documents already exist. Use --force to regenerate.")
        if "--force" not in sys.argv:
            return

    print("Step 1: Download pubmed source")
    jsonl_path = download_pubmed()
    print()

    print("Step 2: Load tokenizer")
    tokenizer = load_tokenizer()
    print()

    print("Step 3: Extract articles")
    articles = extract_articles(jsonl_path)
    print(f"  Extracted {len(articles)} articles from pubmed JSONL")
    print()

    print("Step 4: Generate target-size documents")
    for name, target in TARGET_DOCS.items():
        generate_doc(articles, target, tokenizer, DOCS_DIR / name)
    print()

    print("=== Done ===")


if __name__ == "__main__":
    main()
