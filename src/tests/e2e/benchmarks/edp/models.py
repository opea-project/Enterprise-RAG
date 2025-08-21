import csv
import json
import subprocess  # nosec B404: subprocess is used with controlled input for git commands
from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_serializer
import datetime

class Fileset(str, Enum):
    simple_small = 'SIMPLE_SMALL'
    simple_medium = 'SIMPLE_MEDIUM'
    simple_large = 'SIMPLE_LARGE'
    simple_xlarge = 'SIMPLE_XLARGE'
    moderate_small = 'MODERATE_SMALL'
    moderate_medium = 'MODERATE_MEDIUM'
    moderate_large = 'MODERATE_LARGE'
    moderate_xlarge = 'MODERATE_XLARGE'

class ProcessingKpi(BaseModel):
    """
    Document processing metrics. Each metric is in milliseconds.
    """
    extraction: int
    compression: int
    splitting: int
    dpguard_scan: int
    embedding: int
    ingestion: int
    total: int

class FileInfo(BaseModel):
    file_name: str
    file_size: int # BYTES
    total_chunks: int

class FileProcessing(BaseModel):
    file_info: FileInfo
    timing: ProcessingKpi

class FilesProcessingSeries(BaseModel):
    fileset_name: Fileset
    records: list[FileProcessing] = []
    all_totals: int

    @computed_field
    @property
    def n(self) -> int:
        return len(self.records)

class CommitInfo(BaseModel):
    sha: str = Field(default_factory=lambda: CommitInfo._get_sha(), frozen=True)
    date_time: datetime.datetime = Field(default_factory=lambda: CommitInfo._get_datetime(), frozen=True)
    branch: str = Field(default_factory=lambda: CommitInfo._get_branch(), frozen=True)
    author_name: str = Field(default_factory=lambda: CommitInfo._get_author_name(), frozen=True)
    author_email: str = Field(default_factory=lambda: CommitInfo._get_author_email(), frozen=True)

    @staticmethod
    def _get_sha() -> str:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError(
                f"Command to get current commit SHA failed with return code {result.returncode}.\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

    @staticmethod
    def _get_datetime() -> datetime.datetime:
        result = subprocess.run(
            ['git', 'show', '-s', '--format=%cI', 'HEAD'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            raw_output = result.stdout.strip()
            return datetime.datetime.fromisoformat(raw_output)
        else:
            raise RuntimeError(
                f"Command to get current commit datetime failed with return code {result.returncode}.\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

    @staticmethod
    def _get_branch() -> str:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError(
                f"Command to get current branch failed with return code {result.returncode}.\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

    @staticmethod
    def _get_author_name() -> str:
        result = subprocess.run(['git', 'show', '-s', '--format=%an', 'HEAD'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError(
                f"Command to get current commit author failed with return code {result.returncode}.\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

    @staticmethod
    def _get_author_email() -> str:
        result = subprocess.run(['git', 'show', '-s', '--format=%ae', 'HEAD'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError(
                f"Command to get current commit author email failed with return code {result.returncode}.\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

    @field_serializer('date_time')
    def serialize_date_time(self, dt: datetime.datetime, _info):
        return dt.isoformat()


class EdpRecord(BaseModel):
    timing_series: FilesProcessingSeries
    date_time: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    commit_info: CommitInfo = Field(default_factory=CommitInfo, frozen=True)

    @field_serializer('date_time')
    def serialize_date_time(self, dt: datetime.datetime, _info):
        return dt.isoformat()

    def dump_json(self, path):
        with open(path, "w") as f:
            f.write(json.dumps(self.model_dump()) + "\n")

    def dump_csv(self, csv_path: str):
        """
        Custom export to CSV format.
        """
        rows = []
        for rec in self.timing_series.records:
            row = {
                "file_name": rec.file_info.file_name,
                "file_size": rec.file_info.file_size,
                "total_chunks": rec.file_info.total_chunks,
                "extraction": rec.timing.extraction,
                "compression": rec.timing.compression,
                "splitting": rec.timing.splitting,
                "dpguard_scan": rec.timing.dpguard_scan,
                "embedding": rec.timing.embedding,
                "ingestion": rec.timing.ingestion,
                "total": rec.timing.total,
            }
            rows.append(row)
        field_names = rows[0].keys()

        with open(csv_path, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(rows)

            # Add two empty rows
            writer.writerow({})
            writer.writerow({})

            # Add summary rows
            summary_row = {k: "" for k in field_names}
            summary_row["ingestion"] = "Total benchmark time:"
            summary_row["total"] = self.timing_series.all_totals
            writer.writerow(summary_row)
