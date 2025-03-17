// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export class LinkForIngestion {
  id: string = "";
  value: string = "";
}

export type DataStatus =
  | "uploaded"
  | "error"
  | "processing"
  | "dataprep"
  | "dpguard"
  | "embedding"
  | "ingested"
  | "deleting"
  | "blocked";

export interface FileDataItem {
  id: string;
  bucket_name: string;
  object_name: string;
  size: number;
  etag: string;
  created_at: string;
  chunk_size: number;
  chunks_total: number;
  chunks_processed: number;
  status: DataStatus;
  job_name: string;
  job_message: string;
  dataprep_duration: number;
  embedding_duration: number;
  processing_duration: number;
}

export interface LinkDataItem {
  id: string;
  uri: string;
  created_at: string;
  chunk_size: number;
  chunks_total: number;
  chunks_processed: number;
  status: DataStatus;
  job_name: string;
  job_message: string;
  dataprep_duration: number;
  embedding_duration: number;
  processing_duration: number;
}

export interface UploadErrors {
  files: string;
  links: string;
}
