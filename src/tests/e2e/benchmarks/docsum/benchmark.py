#!/usr/bin/env python3
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import csv
import json
import os
import re
import sys
import threading
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue

_DOMAIN = os.environ.get("ERAG_DOMAIN_NAME", "erag.com")
os.environ["no_proxy"] = os.environ.get("no_proxy", "") + f",{_DOMAIN},auth.{_DOMAIN},localhost,127.0.0.1"
os.environ["NO_PROXY"] = os.environ.get("NO_PROXY", "") + f",{_DOMAIN},auth.{_DOMAIN},localhost,127.0.0.1"

import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_HAS_TRANSFORMERS = False
_FORCE_NO_TOKENIZER = "--no-tokenizer" in sys.argv
if not _FORCE_NO_TOKENIZER:
    try:
        from transformers import AutoTokenizer
        _HAS_TRANSFORMERS = True
    except ImportError:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent


def log(msg, quiet=False):
    if not quiet:
        print(msg, file=sys.stderr, flush=True)


def count_tokens(text, tokenizer):
    if tokenizer is not None:
        return len(tokenizer.encode(text))
    return int(len(text.split()) * 1.3)


def load_tokenizer(model_name, quiet=False):
    if not _HAS_TRANSFORMERS or _FORCE_NO_TOKENIZER:
        log("Using word-count approximation for token counting", quiet)
        return None
    try:
        tok = AutoTokenizer.from_pretrained(
            model_name, token=os.environ.get("HF_TOKEN")
        )
        log(f"Loaded tokenizer: {model_name}", quiet)
        return tok
    except Exception as e:
        log(f"Failed to load tokenizer {model_name}: {e}, falling back to approximation", quiet)
        return None


def truncate_to_tokens(text, target_tokens, tokenizer):
    if tokenizer is not None:
        ids = tokenizer.encode(text)
        if len(ids) <= target_tokens:
            return text
        return tokenizer.decode(ids[:target_tokens], skip_special_tokens=True)
    words = text.split()
    target_words = int(target_tokens / 1.3)
    if len(words) <= target_words:
        return text
    return " ".join(words[:target_words])


def parse_duration(duration_str):
    m = re.match(r'^(\d+)\s*(s|m|h)$', duration_str.strip())
    if not m:
        raise argparse.ArgumentTypeError(
            f"Invalid duration: '{duration_str}'. Use format like '30m', '1h', '90s'."
        )
    value = int(m.group(1))
    unit = m.group(2)
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600


def get_bearer_token(bearer_path):
    return Path(bearer_path).read_text(encoding="utf-8").strip().splitlines()[0].strip()


def refresh_token_file(bearer_path):
    domain = os.environ.get("ERAG_DOMAIN_NAME", "erag.com")
    routing_mode = os.environ.get("ERAG_ROUTING_MODE", "subdomain")
    if routing_mode == "path":
        auth_domain = f"https://{domain}/auth"
    else:
        auth_domain = f"https://auth.{domain}"
    realm = os.environ.get("KEYCLOAK_REALM", "EnterpriseRAG")
    client_id = os.environ.get("KEYCLOAK_CLIENT_ID", "EnterpriseRAG-oidc")
    username = os.environ.get("KEYCLOAK_ERAG_ADMIN_USERNAME", "erag-admin")
    password = os.environ.get("KEYCLOAK_ERAG_ADMIN_PASSWORD", "")
    if not password:
        return False
    token_url = f"{auth_domain}/realms/{realm}/protocol/openid-connect/token"
    try:
        resp = requests.post(token_url, data={
            "username": username, "password": password,
            "grant_type": "password", "client_id": client_id,
        }, verify=False, timeout=10)
        if resp.status_code == 200:
            token = resp.json().get("access_token", "")
            if token:
                Path(bearer_path).write_text(token + "\n")
                return True
    except Exception:
        pass
    return False


def send_request(server, text, bearer_path, summary_type, max_tokens):
    bearer_token = get_bearer_token(bearer_path)
    payload = {
        "files": [],
        "links": [],
        "texts": [text],
        "parameters": {
            "stream": True,
            "summary_type": summary_type,
            "max_new_tokens": max_tokens,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }

    result = {
        "e2e_latency": 0.0,
        "ttft": 0.0,
        "output_tokens": 0,
        "tpot": 0.0,
        "tokens_per_sec": 0.0,
        "map_chunks": 0,
        "reduce_chunks": 0,
        "error": None,
        "answer": "",
    }

    t_start = time.perf_counter()
    first_content_time = None
    answer_parts = []
    map_count = 0
    reduce_count = 0

    try:
        resp = requests.post(
            server, json=payload, headers=headers, stream=True, verify=False, timeout=600
        )
        resp.raise_for_status()

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if not line.startswith("data: "):
                continue

            data_str = line[len("data: "):]

            if data_str.strip() == "[DONE]":
                break

            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            choices = data.get("choices", [])
            if not choices:
                continue

            content = choices[0].get("delta", {}).get("content", "")
            if not content:
                continue

            if first_content_time is None:
                first_content_time = time.perf_counter()

            intermediate_map = re.findall(r"\[INTERMEDIATE_MAP_\d+\]", content)
            intermediate_reduce = re.findall(r"\[INTERMEDIATE_REDUCE_\d+\]", content)
            map_count += len(intermediate_map)
            reduce_count += len(intermediate_reduce)

            cleaned = re.sub(r"\[INTERMEDIATE_MAP_\d+\]", "", content)
            cleaned = re.sub(r"\[INTERMEDIATE_REDUCE_\d+\]", "", cleaned)
            if cleaned:
                answer_parts.append(cleaned)

        t_end = time.perf_counter()
        e2e = t_end - t_start
        ttft = (first_content_time - t_start) if first_content_time else e2e

        result["e2e_latency"] = e2e
        result["ttft"] = ttft
        result["map_chunks"] = map_count
        result["reduce_chunks"] = reduce_count
        result["answer"] = "".join(answer_parts)

    except Exception as e:
        t_end = time.perf_counter()
        result["e2e_latency"] = t_end - t_start
        result["ttft"] = 0.0
        result["error"] = str(e)

    return result


def _process_result(res, tokenizer):
    output_tokens = count_tokens(res["answer"], tokenizer) if res["answer"] else 0
    res["output_tokens"] = output_tokens
    generation_time = res["e2e_latency"] - res["ttft"]
    if output_tokens > 0 and generation_time > 0:
        res["tpot"] = generation_time / output_tokens
        res["tokens_per_sec"] = output_tokens / generation_time
    else:
        res["tpot"] = 0.0
        res["tokens_per_sec"] = 0.0
    return res


def _write_row(writer, csvfile, res, args, run_idx, input_tokens):
    writer.writerow([
        Path(args.file).name,
        args.concurrency, run_idx, input_tokens, res["output_tokens"],
        f"{res['e2e_latency']:.4f}", f"{res['ttft']:.4f}",
        f"{res['tpot']:.6f}", f"{res['tokens_per_sec']:.2f}",
        res["map_chunks"], res["reduce_chunks"],
        res["error"] or "",
    ])
    csvfile.flush()


def _run_repetition_mode(args, document_text, bearer_path, input_tokens, tokenizer,
                         csv_path, csv_header, quiet):
    all_results = []
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, lineterminator="\n")
        writer.writerow(csv_header)

        for run_idx in range(1, args.runs + 1):
            refresh_token_file(bearer_path)
            log(f"Run {run_idx}/{args.runs} (concurrency={args.concurrency})", quiet)

            futures = []
            with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                for _ in range(args.concurrency):
                    fut = executor.submit(
                        send_request, args.server, document_text, bearer_path,
                        args.summary_type, args.max_tokens
                    )
                    futures.append(fut)

                for fut in as_completed(futures):
                    res = _process_result(fut.result(), tokenizer)
                    _write_row(writer, csvfile, res, args, run_idx, input_tokens)
                    all_results.append(res)

                    if res["error"]:
                        log(f"  Error: {res['error']}", quiet)
                    else:
                        log(f"  e2e={res['e2e_latency']:.2f}s ttft={res['ttft']:.3f}s "
                            f"tokens/s={res['tokens_per_sec']:.1f} out_tok={res['output_tokens']}", quiet)
    return all_results


def _duration_worker(wid, stop_event, args, document_text, bearer_path, input_tokens,
                     tokenizer, result_queue, quiet):
    run_idx = 0
    while not stop_event.is_set():
        run_idx += 1
        if run_idx % 10 == 1:
            refresh_token_file(bearer_path)
        res = send_request(args.server, document_text, bearer_path,
                           args.summary_type, args.max_tokens)
        if stop_event.is_set():
            break
        res = _process_result(res, tokenizer)
        result_queue.put((wid, run_idx, res))
        if res["error"]:
            log(f"  [{wid}] Error: {res['error']}", quiet)
        else:
            log(f"  [{wid}] e2e={res['e2e_latency']:.2f}s ttft={res['ttft']:.3f}s "
                f"tokens/s={res['tokens_per_sec']:.1f} out_tok={res['output_tokens']}", quiet)


def _run_duration_mode(args, document_text, bearer_path, input_tokens, tokenizer,
                       csv_path, csv_header, quiet):
    all_results = []
    stop_event = threading.Event()
    result_queue = Queue()

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, lineterminator="\n")
        writer.writerow(csv_header)

        threads = []
        for wid in range(args.concurrency):
            t = threading.Thread(
                target=_duration_worker,
                args=(wid, stop_event, args, document_text, bearer_path,
                      input_tokens, tokenizer, result_queue, quiet),
                daemon=True,
            )
            t.start()
            threads.append(t)

        start_time = time.perf_counter()
        while time.perf_counter() - start_time < args.duration:
            try:
                wid, run_idx, res = result_queue.get(timeout=1.0)
                _write_row(writer, csvfile, res, args, run_idx, input_tokens)
                all_results.append(res)
            except Empty:
                continue

        stop_event.set()
        for t in threads:
            t.join(timeout=30)

        while not result_queue.empty():
            try:
                wid, run_idx, res = result_queue.get_nowait()
                _write_row(writer, csvfile, res, args, run_idx, input_tokens)
                all_results.append(res)
            except Empty:
                break

    elapsed = time.perf_counter() - start_time
    log(f"Duration mode completed: {elapsed:.0f}s, {len(all_results)} requests", quiet)
    return all_results


def run_benchmark(args):
    document_text = Path(args.file).read_text(encoding="utf-8")
    bearer_path = args.bearer
    quiet = args.quiet

    tokenizer = load_tokenizer(args.model, quiet)

    if args.input_tokens:
        document_text = truncate_to_tokens(document_text, args.input_tokens, tokenizer)
        log(f"Truncated document to ~{args.input_tokens} input tokens", quiet)

    input_tokens = count_tokens(document_text, tokenizer)
    log(f"Document: {args.file} ({input_tokens} input tokens)", quiet)
    log(f"Server: {args.server}", quiet)
    log(f"Summary type: {args.summary_type}, max tokens: {args.max_tokens}", quiet)

    duration_mode = args.duration is not None
    if duration_mode:
        log(f"Mode: duration ({args.duration}s), concurrency: {args.concurrency}", quiet)
    else:
        log(f"Mode: repetitions ({args.runs}), concurrency: {args.concurrency}", quiet)

    refresh_token_file(bearer_path)
    log("Warmup request...", quiet)
    warmup = send_request(args.server, document_text, bearer_path, args.summary_type, args.max_tokens)
    if warmup["error"]:
        log(f"Warmup failed: {warmup['error']}", quiet)
    else:
        log(f"Warmup complete (e2e={warmup['e2e_latency']:.2f}s)", quiet)

    if args.output:
        csv_path = args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = str(SCRIPT_DIR / "results" / f"docsum_bench_{ts}.csv")

    all_results = []
    csv_header = [
        "source_file", "concurrency", "run", "input_tokens", "output_tokens",
        "e2e_latency", "ttft", "tpot", "tokens_per_sec",
        "map_chunks", "reduce_chunks", "error",
    ]

    if duration_mode:
        all_results = _run_duration_mode(
            args, document_text, bearer_path, input_tokens, tokenizer,
            csv_path, csv_header, quiet,
        )
    else:
        all_results = _run_repetition_mode(
            args, document_text, bearer_path, input_tokens, tokenizer,
            csv_path, csv_header, quiet,
        )

    log(f"\nResults written to: {csv_path}", quiet)

    successful = [r for r in all_results if r["error"] is None]
    if successful:
        n = len(successful)
        avg_tps = sum(r["tokens_per_sec"] for r in successful) / n
        avg_e2e = sum(r["e2e_latency"] for r in successful) / n
        avg_ttft = sum(r["ttft"] for r in successful) / n
        avg_tpot = sum(r["tpot"] for r in successful) / n

        if not quiet:
            print(flush=True)
            print(f"{'Concurrency':<13}{'Tokens/sec':<12}{'E2elatency(s)':<16}{'TTFT(s)':<10}{'TPOT(s)':<10}")
            print(f"{args.concurrency:<13}{avg_tps:<12.1f}{avg_e2e:<16.1f}{avg_ttft:<10.3f}{avg_tpot:<10.3f}")

        if args.json_summary:
            summary = {
                "concurrency": args.concurrency,
                "runs": n,
                "input_tokens": input_tokens,
                "avg_e2e_latency": round(avg_e2e, 2),
                "avg_ttft": round(avg_ttft, 3),
                "avg_tpot": round(avg_tpot, 4),
                "avg_tokens_per_sec": round(avg_tps, 1),
                "avg_output_tokens": round(sum(r["output_tokens"] for r in successful) / n),
                "avg_map_chunks": round(sum(r["map_chunks"] for r in successful) / n),
                "total_runs": n,
                "errors": len(all_results) - n,
                "csv_path": csv_path,
            }
            if duration_mode:
                summary["duration_seconds"] = args.duration
            print(json.dumps(summary))
    else:
        log("All requests failed, no summary available", quiet)
        if args.json_summary:
            print(json.dumps({"error": "all_failed", "total_runs": 0, "errors": len(all_results)}))
        sys.exit(1)


def main():
    default_server = os.environ.get(
        "ERAG_DOCSUM_URL",
        f"https://{os.environ.get('ERAG_DOMAIN_NAME', 'erag.com')}/api/v1/docsum"
    )
    default_model = os.environ.get("BENCHMARK_TOKENIZER", "casperhansen/llama-3-8b-instruct-awq")
    default_bearer = str(SCRIPT_DIR / ".bearer")

    parser = argparse.ArgumentParser(description="DocSum pipeline E2E benchmark")
    parser.add_argument("-s", "--server", default=default_server,
                        help="DocSum API URL")
    parser.add_argument("-f", "--file", required=True,
                        help="Path to document file to summarize")
    parser.add_argument("-c", "--concurrency", type=int, default=1,
                        help="Number of concurrent requests")
    parser.add_argument("-r", "--runs", type=int, default=3,
                        help="Number of repetitions (mutually exclusive with -d)")
    parser.add_argument("-d", "--duration", type=str, default=None,
                        help="Run for a duration instead of fixed repetitions (e.g. 30m, 1h, 90s)")
    parser.add_argument("-t", "--summary-type", default="map_reduce",
                        choices=["map_reduce", "stuff", "refine"],
                        help="Summarization strategy")
    parser.add_argument("-m", "--model", default=default_model,
                        help="HuggingFace model name for tokenizer")
    parser.add_argument("--max-tokens", type=int, default=1024,
                        help="Max output tokens")
    parser.add_argument("-x", "--input-tokens", type=int, default=None,
                        help="Truncate document to N input tokens")
    parser.add_argument("-o", "--output", default=None,
                        help="Output CSV file path")
    parser.add_argument("-b", "--bearer", default=default_bearer,
                        help="Path to bearer token file")
    parser.add_argument("--no-tokenizer", action="store_true",
                        help="Skip HuggingFace tokenizer, use word-count approximation")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress progress output")
    parser.add_argument("--json-summary", action="store_true",
                        help="Print JSON metrics summary at end")

    args = parser.parse_args()

    if args.duration and args.runs != 3:
        parser.error("-d/--duration and -r/--runs are mutually exclusive")
    if args.duration:
        args.duration = parse_duration(args.duration)

    if not Path(args.file).is_file():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.bearer).is_file():
        if not refresh_token_file(args.bearer):
            print(f"Error: bearer token file not found: {args.bearer}", file=sys.stderr)
            print("Set KEYCLOAK_ERAG_ADMIN_PASSWORD or use ../chatqa/generate_uat_to_file.sh first", file=sys.stderr)
            sys.exit(1)

    run_benchmark(args)


if __name__ == "__main__":
    main()
