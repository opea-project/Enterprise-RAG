# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.database import Base
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field

class UserIdentity(BaseModel):
  principalId: Optional[str] = None

class Bucket(BaseModel):
  name: Optional[str] = None
  ownerIdentity: Optional[UserIdentity] = None
  arn: Optional[str] = None

class Object(BaseModel):
  key: Optional[str] = None
  size: Optional[int] = None
  eTag: Optional[str] = None
  contentType: Optional[str] = None
  userMetadata: Optional[dict] = None
  sequencer: Optional[str] = None

class S3(BaseModel):
  s3SchemaVersion: str
  configurationId: str
  bucket: Bucket
  object: Object

class Source(BaseModel):
  host: str
  port: Optional[str] = None
  userAgent: str

class Record(BaseModel):
  eventVersion: str
  eventSource: str
  awsRegion: str
  eventTime: str
  eventName: str
  userIdentity: UserIdentity
  s3: S3
  source: Source

class S3UserIdentity(BaseModel):
  principalId: str

class S3RequestParameters(BaseModel):
  sourceIPAddress: str

class S3ResponseElements(BaseModel):
  x_amz_request_id: str = Field(alias="x-amz-request-id")
  x_amz_id_2: str = Field(alias="x-amz-request-id")

class S3OwnerIdentity(BaseModel):
  principalId: str

class S3Bucket(BaseModel):
  name: str
  ownerIdentity: S3OwnerIdentity
  arn: str

class S3Object(BaseModel):
  key: str
  size: Optional[int] = ""
  eTag: Optional[str] = ""
  sequencer: str
  contentType: Optional[str] = ""

class S3(BaseModel):
  s3SchemaVersion: str
  configurationId: str
  bucket: S3Bucket
  object: S3Object

class S3Record(BaseModel):
  eventVersion: str
  eventSource: str
  awsRegion: str
  eventTime: str
  eventName: str
  userIdentity: S3UserIdentity
  requestParameters: Optional[S3RequestParameters] = None
  responseElements: Optional[S3ResponseElements] = None
  s3: S3

class S3EventData(BaseModel):
  Records: List[S3Record]

class MinioEventData(BaseModel):
  EventName: Optional[str] = None
  Key: Optional[str] = None
  Records: List[Record]

class PresignedRequest(BaseModel):
    bucket_name: str
    object_name: str
    method: str

class LinkRequest(BaseModel):
    links: List[str]

class PresignedResponse(BaseModel):
   url: str

class ObjectResponse(BaseModel):
    id: str
    created_at: datetime
    chunk_size: int
    chunks_total: int
    chunks_processed: int
    status: str
    job_name: str
    job_message: str
    job_start_time: int
    text_extractor_duration: int
    text_compression_duration: int
    text_splitter_duration: int
    dpguard_duration: int
    embedding_duration: int
    ingestion_duration: int
    processing_duration: int

class FileResponse(ObjectResponse):
    id: str
    bucket_name: str
    object_name: str
    size: int
    etag: str

class LinkResponse(ObjectResponse):
    id: str
    uri: str

class ObjectStatus(Base):
    __abstract__ = True # SQLAlchemy skip table creation

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    status = Column(String, index=False) # uploaded, error, processing, text_extracting, text_compression, text_splitting, dpguard, embedding, ingested, deleting, canceled, blocked
    job_name = Column(String, index=False) # file_processing_job, file_deleting_job
    job_message = Column(String, index=False)

    chunk_size = Column(Integer, index=False, default=0)
    chunks_total = Column(Integer, index=False, default=0)
    chunks_processed = Column(Integer, index=False, default=0)

    text_extractor_start = Column(DateTime, index=False)
    text_extractor_end = Column(DateTime, index=False)
    text_compression_start = Column(DateTime, index=False)
    text_compression_end = Column(DateTime, index=False)
    text_splitter_start = Column(DateTime, index=False)
    text_splitter_end = Column(DateTime, index=False)
    dpguard_start = Column(DateTime, index=False)
    dpguard_end = Column(DateTime, index=False)
    embedding_start = Column(DateTime, index=False)
    embedding_end = Column(DateTime, index=False)
    ingestion_start = Column(DateTime, index=False)
    ingestion_end = Column(DateTime, index=False)

    task_id = Column(String, index=False)
    marked_for_deletion = Column(Boolean, index=False, default=False)

    def to_response(self, class_type, **kwargs):
        def format_duration(start, end, multiplier=1_000):
            # multiplier 1_000_000 for microseconds, 1_000 for milliseconds, 1 for seconds
            if end and start:
                return int((end - start).total_seconds() * multiplier)
            return 0
        def format_timestamp(datetime, multipier=1):
            # multiplier 1_000_000 for microseconds, 1_000 for milliseconds, 1 for seconds
            if datetime:
                return int(datetime.timestamp() * multipier)
            return 0
        text_extractor_duration = format_duration(self.text_extractor_start, self.text_extractor_end)
        text_compression_duration = format_duration(self.text_compression_start, self.text_compression_end)
        text_splitter_duration = format_duration(self.text_splitter_start, self.text_splitter_end)
        dpguard_duration = format_duration(self.dpguard_start, self.dpguard_end)
        embedding_duration = format_duration(self.embedding_start, self.embedding_end)
        ingestion_duration = format_duration(self.ingestion_start, self.ingestion_end)
        return class_type(
            id=str(self.id),
            created_at=self.created_at or datetime.now(timezone.utc),
            chunk_size=self.chunk_size or 0,
            chunks_total=self.chunks_total or 0,
            chunks_processed=self.chunks_processed or 0,
            status=self.status or "",
            job_name=self.job_name or "",
            job_message=self.job_message or "",
            job_start_time=format_timestamp(self.text_extractor_start),
            text_extractor_duration=text_extractor_duration,
            text_compression_duration=text_compression_duration,
            text_splitter_duration=text_splitter_duration,
            dpguard_duration=dpguard_duration,
            embedding_duration=embedding_duration,
            ingestion_duration=ingestion_duration,
            processing_duration=text_extractor_duration+text_compression_duration+text_splitter_duration+embedding_duration+ingestion_duration,
            **kwargs
        )

class FileStatus(ObjectStatus):
    __tablename__ = "files"

    bucket_name = Column(String, index=True)
    object_name = Column(String, index=True)
    etag = Column(String, index=False)
    content_type = Column(String, index=False)
    size = Column(Integer, index=False)

    def to_response(self):
      obj = super().to_response(
        FileResponse,
        bucket_name = self.bucket_name,
        object_name = self.object_name,
        etag = self.etag or "",
        size = self.size or 0,
      )
      return obj

class LinkStatus(ObjectStatus):
    __tablename__ = "links"

    uri = Column(String, index=True)

    def to_response(self):
      obj = super().to_response(
        LinkResponse,
        uri = self.uri
      )
      return obj
