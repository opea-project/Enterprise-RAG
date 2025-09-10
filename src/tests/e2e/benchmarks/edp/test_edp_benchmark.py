import asyncio
import json
import os
import shutil

import pytest
import time

from models import ProcessingKpi, FileProcessing, FileInfo, FilesProcessingSeries, EdpRecord, Fileset

# Relative to tox chdir. See tox.ini :: testenv:benchmark_edp
FILES_DIR = "e2e/benchmarks/edp/files"
RESULTS_DIR = "e2e/benchmarks/edp/results"

# Generate dataset names like simple_small, moderate_xlarge etc.
complexities = ("simple", "moderate")
sizes = ("small", "medium", "large", "xlarge")
datasets_names = (f"{c}_{s}" for s in sizes for c in complexities)

@pytest.fixture(scope="session", autouse=True)
def ensure_results_dir() -> None:
    """Idepotent fixture to have clean directory for results."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    for filename in os.listdir(RESULTS_DIR):
        file_path = os.path.join(RESULTS_DIR, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


@pytest.mark.parametrize("ds_name", datasets_names)
def test_edp_benchmark(edp_helper, ds_name):
    dataset_dir = os.path.join(FILES_DIR, ds_name)
    dataset_files_names = [
        f for f in os.listdir(dataset_dir)
        if os.path.isfile(os.path.join(dataset_dir, f))
    ]

    time_start = time.perf_counter()
    edp_helper.upload_files_in_parallel(dataset_dir, dataset_files_names)
    try:
        edp_helper.wait_for_all_files_ingestion(set(dataset_files_names), 36000)
        time_total = int((time.perf_counter() - time_start) * 1000)

        series = FilesProcessingSeries(
            fileset_name=Fileset(ds_name.upper()),
            all_totals=time_total
        )
        edp_results = edp_helper.list_files().json()
        for file_name in dataset_files_names:
            file_processing = get_file_edp_data(edp_results, file_name)
            series.records.append(file_processing)
        benchmark_record = EdpRecord(
            timing_series=series
        )

        print(json.dumps(benchmark_record.model_dump(), indent=4))
        benchmark_record.dump_csv(os.path.join(RESULTS_DIR, f"{ds_name}_benchmark.csv"))
        benchmark_record.dump_json(os.path.join(RESULTS_DIR, f"{ds_name}_benchmark.json"))
    finally:
        delete_files_from_edp(edp_helper, dataset_files_names)


def get_file_edp_data(edp_results, filename):
        file_found = False
        for file in edp_results:
            if file.get("object_name") == filename:
                file_found = True
                file_size = file.get("size")
                total_chunks = file.get("chunks_total")
                file_info = FileInfo(
                    file_name=filename,
                    file_size=file_size,
                    total_chunks=total_chunks
                )
                data = ProcessingKpi(
                    extraction=file.get("text_extractor_duration"),
                    compression=file.get("text_compression_duration"),
                    splitting=file.get("text_splitter_duration"),
                    dpguard_scan=file.get("dpguard_duration"),
                    embedding=file.get("embedding_duration"),
                    ingestion=file.get("ingestion_duration"),
                    total=file.get("processing_duration"),
                )
                file_processing = FileProcessing(
                file_info=file_info,
                timing=data
                )
                return file_processing

        if not file_found:
            print(f"File {filename} is not present in the list of files")


def delete_files_from_edp(edp_helper, file_name_list):
    presigned_urls = asyncio.run(edp_helper.generate_many_presigned_urls(file_name_list, "DELETE"))
    presigned_urls_list = list(presigned_urls.values())
    asyncio.run(edp_helper.delete_many_files(presigned_urls_list))
