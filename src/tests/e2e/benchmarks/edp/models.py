import csv
import json
from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_serializer
import datetime

class Fileset(str, Enum):
    simple_small = 'SIMPLE_SMALL'
    simple_medium = 'SIMPLE_MEDIUM'
    simple_large = 'SIMPLE_LARGE'
    moderate_small = 'MODERATE_SMALL'
    moderate_medium = 'MODERATE_MEDIUM'
    moderate_large = 'MODERATE_LARGE'

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
    # file_size: int

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

class EdpRecord(BaseModel):
    timing_series: FilesProcessingSeries
    date_time: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

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
