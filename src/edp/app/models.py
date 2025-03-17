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

class FileResponse(BaseModel):
    id: str
    bucket_name: str
    object_name: str
    size: int
    etag: str
    created_at: datetime
    chunk_size: int
    chunks_total: int
    chunks_processed: int
    status: str
    job_name: str
    job_message: str
    dataprep_duration: int
    dpguard_duration: int
    embedding_duration: int
    processing_duration: int

class LinkResponse(BaseModel):
    id: str
    uri: str
    created_at: datetime
    chunk_size: int
    chunks_total: int
    chunks_processed: int
    status: str
    job_name: str
    job_message: str
    dataprep_duration: int
    dpguard_duration: int
    embedding_duration: int
    processing_duration: int

class FileStatus(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    bucket_name = Column(String, index=True)
    object_name = Column(String, index=True)
    etag = Column(String, index=False)
    content_type = Column(String, index=False)
    size = Column(Integer, index=False)

    status = Column(String, index=False) # uploaded, error, processing, dataprep, dpguard, embedding, ingested, deleting, canceled, blocked
    job_name = Column(String, index=False) # file_processing_job, file_deleting_job
    job_message = Column(String, index=False)
    
    chunk_size = Column(Integer, index=False, default=0)
    chunks_total = Column(Integer, index=False, default=0)
    chunks_processed = Column(Integer, index=False, default=0)
    
    dataprep_start = Column(DateTime, index=False)
    dataprep_end = Column(DateTime, index=False)
    dpguard_start = Column(DateTime, index=False)
    dpguard_end = Column(DateTime, index=False)
    embedding_start = Column(DateTime, index=False)
    embedding_end = Column(DateTime, index=False)

    task_id = Column(String, index=False)
    marked_for_deletion = Column(Boolean, index=False, default=False)

    def to_response(self):
        dataprep_duration = int((self.dataprep_end - self.dataprep_start).total_seconds()) if self.dataprep_end and self.dataprep_start else 0
        dpguard_duration = int((self.dpguard_end - self.dpguard_start).total_seconds()) if self.dpguard_end and self.dpguard_start else 0
        embedding_duration = int((self.embedding_end - self.embedding_start).total_seconds()) if self.embedding_end and self.embedding_start else 0
        return FileResponse(
            id=str(self.id),
            bucket_name=self.bucket_name,
            object_name=self.object_name,
            etag=self.etag or "",
            size=self.size or 0,
            created_at=self.created_at or datetime.now(timezone.utc),
            chunk_size=self.chunk_size or 0,
            chunks_total=self.chunks_total or 0,
            chunks_processed=self.chunks_processed or 0,
            status=self.status or "",
            job_name=self.job_name or "",
            job_message=self.job_message or "",
            dataprep_duration=dataprep_duration,
            dpguard_duration=dpguard_duration,
            embedding_duration=embedding_duration,
            processing_duration=dataprep_duration+embedding_duration
        )

class LinkStatus(Base):
    __tablename__ = "links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    uri = Column(String, index=True)

    status = Column(String, index=False) # uploaded, error, processing, dataprep, dpguard, embedding, ingested, deleting, blocked
    job_name = Column(String, index=False) # link_processing_job, link_deleting_job
    job_message = Column(String, index=False)

    chunk_size = Column(Integer, index=False, default=0)
    chunks_total = Column(Integer, index=False, default=0)
    chunks_processed = Column(Integer, index=False, default=0)

    dataprep_start = Column(DateTime, index=False)
    dataprep_end = Column(DateTime, index=False)
    dpguard_start = Column(DateTime, index=False)
    dpguard_end = Column(DateTime, index=False)
    embedding_start = Column(DateTime, index=False)
    embedding_end = Column(DateTime, index=False)

    task_id = Column(String, index=False)
    marked_for_deletion = Column(Boolean, index=False, default=False)

    def to_response(self):
      dataprep_duration = int((self.dataprep_end - self.dataprep_start).total_seconds()) if self.dataprep_end and self.dataprep_start else 0
      dpguard_duration = int((self.dpguard_end - self.dpguard_start).total_seconds()) if self.dpguard_end and self.dpguard_start else 0
      embedding_duration = int((self.embedding_end - self.embedding_start).total_seconds()) if self.embedding_end and self.embedding_start else 0

      return LinkResponse(
            id=str(self.id),
            uri=self.uri,
            created_at=self.created_at or datetime.now(timezone.utc),
            chunk_size=self.chunk_size or 0,
            chunks_total=self.chunks_total or 0,
            chunks_processed=self.chunks_processed or 0,
            status=self.status or "",
            job_name=self.job_name or "",
            job_message=self.job_message or "",
            dataprep_duration=dataprep_duration,
            dpguard_duration=dpguard_duration,
            embedding_duration=embedding_duration,
            processing_duration=dataprep_duration+embedding_duration
        )
