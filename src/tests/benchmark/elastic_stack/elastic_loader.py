import argparse
import copy
import csv
import json
import logging
import os
import re
from datetime import datetime

from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

TRANSFORMATION_MAPPINGS = {
    "datetime": (),
    "cpuset_mems": ("deployment", "docker_conf_changes"),
    "privileged": ("deployment", "docker_conf_changes"),
    "VLLM_TP_SIZE": ("deployment", "env_var_changes"),
    "LLM_CONNECTOR": ("deployment", "env_var_changes"),
    "HABANA_VISIBLE_DEVICES": ("deployment", "env_var_changes"),
    "NUM_SHARD": ("deployment", "env_var_changes"),
    "SHARDED": ("deployment", "env_var_changes"),
    "LLM_VLLM_MODEL_NAME": ("deployment", "env_var_changes"),
    "VLLM_CPU_OMP_THREADS_BIND": ("deployment", "env_var_changes"),
    "service": ("benchmark_parameters",),
    "streaming": ("benchmark_parameters",),
    "input_token_num": ("benchmark_parameters",),
    "max_new_tokens": ("benchmark_parameters",),
    "num_burst_requests": ("benchmark_parameters",),
    "total_time_avg": ("kpis",),
    "total_time_p50": ("kpis",),
    "total_time_p90": ("kpis",),
    "total_time_p99": ("kpis",),
    "second+_avg": ("kpis",),
    "second+_p50": ("kpis",),
    "second+_p90": ("kpis",),
    "second+_p99": ("kpis",),
    "decode_throughput_avg": ("kpis",),
    "first_token_avg": ("kpis",),
    "notes": ("kpis",),
    "prefill_throughput_avg": ("kpis",),
    "received_tokens_avg": ("kpis",),
}


def access_or_set_nested_dict(d, keys, value=None):
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    if value is not None:
        d[keys[-1]] = value
    return d[keys[-1]]


def validate_datetime(strdatetime: str) -> datetime.date:
    """Validates if datetime is in ISO 8601 format like 2024-08-01T14:39:28+10:00."""
    iso8601_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$"
    if strdatetime is None:
        raise ValueError("Datetime is not filled")
    if re.match(iso8601_pattern, strdatetime):
        return datetime.fromisoformat(strdatetime)
    else:
        raise ValueError(f"Cannot parse ISO datetime: {strdatetime}")


def parse_bool(strbool) -> bool:
    if strbool in ["true", "TRUE", "True"]:
        return True

    if strbool in ["false", "FALSE", "False"]:
        return False

    raise ValueError(f"Cannot parse boolean value: {strbool}")


def main():
    parser = argparse.ArgumentParser(description="Elastic Loader Script")
    parser.add_argument("file_path", type=str, help="Path to the CSV file")
    parser.add_argument(
        "--component",
        type=str,
        required=True,
        choices=["llm"],
        help='Component name (only "llm" is accepted)',
    )
    parser.add_argument(
        "--model-server",
        type=str,
        choices=["vllmip_cpu", "vllm_hpu"],
        help="Model server name",
    )
    parser.add_argument("--commit-sha", type=str, help="Commit SHA")
    parser.add_argument("--branch-name", type=str, help="Branch name")
    parser.add_argument("--main-commit-sha", type=str, help="Main commit SHA", required=True)
    parser.add_argument("--server-url", type=str, help="Uploading to server url", required=True)
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt and upload immediately",
    )

    args = parser.parse_args()

    commit_info = {
        "commit_sha": args.commit_sha,
        "branch_name": args.branch_name,
        "main_sha": args.main_commit_sha,
    }

    file = args.file_path
    component = args.component
    model_server = args.model_server
    server_url = args.server_url

    client = Elasticsearch(
        f"https://{server_url}:9200", verify_certs=False, basic_auth=("elastic", "changeme")
    )

    results_doc_base = {
        "source_document": os.path.basename(file),
        "deployment": {},
        "benchmark_parameters": {},
        "kpis": {},
        "commit_info": commit_info,
        "datetime": None,
        "target": {
            "component": component,
            "model_server": model_server,
        },
    }

    documents = []
    filename = os.path.basename(file)

    with open(file, mode="r+") as file:
        csvFile = csv.DictReader(file)
        datetime_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2})', filename)

        if datetime_match:
            upload_datetime = datetime_match.group(1)
        else:
            current_time = datetime.datetime.now()
            upload_datetime = current_time.strftime("%Y-%m-%d %H-%M-%S")
            logger.info(f"Datetime not found in filename: {filename}. Using current time: {upload_datetime}")

        for csv_record in csvFile:
            db_record = copy.deepcopy(results_doc_base)
            db_record['datetime'] = convert_to_iso8601(upload_datetime)

            for key, value in csv_record.items():
                try:
                    new_record_index = TRANSFORMATION_MAPPINGS[key]
                except KeyError as e:
                    logger.error(f"CSV header without mapping: {str(e)}")
                    raise

                if new_record_index == "kpis":
                    try:
                        value = float(value)
                    except ValueError:  # note field is str and cannot convert
                        pass

                if key == "streaming":
                    value = parse_bool(value)

                new_record_index += (key,)
                access_or_set_nested_dict(db_record, new_record_index, value)

            validate_datetime(db_record["datetime"])
            documents.append(db_record)

    documents_debug = json.dumps(documents, indent=4, sort_keys=True)
    logger.info(documents_debug)

    if not args.yes:
        print("About to upload following documents:")
        print(documents_debug)
        confirm = input(
            "Do you want to upload the documents? (Type y or yes to confirm): "
        ).lower()
        if confirm not in ["y", "yes"]:
            print("Upload cancelled.")
            return

    for doc in documents:
        client.index(index="benchmarks", document=doc)
    print("Uploaded.")

def convert_to_iso8601(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H-%M-%S")
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # Appends 'Z' for UTC time

if __name__ == "__main__":
    main()
