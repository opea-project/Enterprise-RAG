import asyncio
import json
import os
import shutil

import pytest
import time

from models import ProcessingKpi, FileProcessing, FileInfo, FilesProcessingSeries, EdpRecord, Fileset

# Relative to tox chdir. See tox.ini :: testenv:benchmark_edp
FILES_DIR = "benchmarks/edp/files"
RESULTS_DIR = "benchmarks/edp/results"

s_extensions = ["adoc", "docx", "md", "pdf", "pptx", "txt", "xlsx"]
ss_file_name = "SS_simple"
sm_file_name = "SM_simple"
sl_file_name = "SL_simple"
ss_files = [f"{ss_file_name}.{extension}" for extension in s_extensions]
sm_files = [f"{sm_file_name}.{extension}" for extension in s_extensions]
sl_files = [f"{sl_file_name}.{extension}" for extension in s_extensions]
m_extensions = ["docx", "pdf", "pptx"]
ms_file_name = "MS_moderate"
mm_file_name = "MM_moderate"
ml_file_name = "ML_moderate"
ms_files = [f"{ms_file_name}.{extension}" for extension in m_extensions]
mm_files = [f"{mm_file_name}.{extension}" for extension in m_extensions]
ml_files = [f"{ml_file_name}.{extension}" for extension in m_extensions]

files_dataset = [(Fileset.simple_small.value, ss_files), (Fileset.simple_medium.value, sm_files), (Fileset.simple_large.value, sl_files),
                 (Fileset.moderate_small.value, ms_files), (Fileset.moderate_medium.value, mm_files), (Fileset.moderate_large.value, ml_files)]

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


@pytest.mark.parametrize("label,dataset", files_dataset, ids=[label for label, _ in files_dataset])
def test_edp_benchmark(edp_helper, label, dataset):
    time_start = time.perf_counter()
    edp_helper.upload_files_in_parallel(FILES_DIR, dataset)
    asyncio.run(async_wait_for_all_files_upload(edp_helper, dataset))
    time_total = int((time.perf_counter() - time_start) * 1000)

    series = FilesProcessingSeries(
        fileset_name=label,
        all_totals=time_total
    )
    edp_results = edp_helper.list_files().json()
    for file in dataset:
        info = FileInfo(file_name=file)
        kpi = get_file_edp_data(edp_results, file)
        file_processing = FileProcessing(
             file_info=info,
             timing=kpi
        )
        series.records.append(file_processing)
    benchmark_record = EdpRecord(
        timing_series=series
    )

    print(json.dumps(benchmark_record.model_dump(), indent=4))
    benchmark_record.dump_csv(os.path.join(RESULTS_DIR, f"{label}_benchmark.csv"))
    benchmark_record.dump_json(os.path.join(RESULTS_DIR, f"{label}_benchmark.json"))
    delete_files_from_edp(edp_helper, dataset)


async def async_wait_for_all_files_upload(edp_helper, files):
    tasks = [async_wait_for_file_upload(edp_helper, file) for file in files]
    await asyncio.gather(*tasks)


async def async_wait_for_file_upload(edp_helper, file):
    result = await asyncio.to_thread(edp_helper.wait_for_file_upload, file, "ingested")
    return result


def get_file_edp_data(edp_results, filename):
        file_found = False
        for file in edp_results:
            if file.get("object_name") == filename:
                file_found = True
                data = ProcessingKpi(
                    extraction=file.get("text_extractor_duration"),
                    compression=file.get("text_compression_duration"),
                    splitting=file.get("text_splitter_duration"),
                    dpguard_scan=file.get("dpguard_duration"),
                    embedding=file.get("embedding_duration"),
                    ingestion=file.get("ingestion_duration"),
                    total=file.get("processing_duration"),
                )
                return data

        if not file_found:
            print(f"File {filename} is not present in the list of files")


def delete_files_from_edp(edp_helper, file_name_list):
    for file_name in file_name_list:
        response = edp_helper.generate_presigned_url(file_name, "DELETE")
        edp_helper.delete_file(response.json().get("url"))