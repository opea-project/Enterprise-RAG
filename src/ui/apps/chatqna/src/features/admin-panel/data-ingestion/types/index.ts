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
  | "text_extracting"
  | "text_compression"
  | "text_splitting"
  | "dpguard"
  | "late_chunking"
  | "embedding"
  | "ingested"
  | "deleting"
  | "canceled"
  | "blocked";

export interface FileDataItem {
  id: string;
  created_at: string;
  chunk_size: number;
  chunks_total: number;
  chunks_processed: number;
  status: DataStatus;
  job_name: string;
  job_message: string;
  job_start_time: number;
  text_extractor_duration: number;
  text_compression_duration: number;
  text_splitter_duration: number;
  dpguard_duration: number;
  late_chunking_duration: number;
  embedding_duration: number;
  ingestion_duration: number;
  processing_duration: number;
  bucket_name: string;
  object_name: string;
  size: number;
  etag: string;
}

export interface LinkDataItem {
  id: string;
  created_at: string;
  chunk_size: number;
  chunks_total: number;
  chunks_processed: number;
  status: DataStatus;
  job_name: string;
  job_message: string;
  job_start_time: number;
  text_extractor_duration: number;
  text_compression_duration: number;
  text_splitter_duration: number;
  dpguard_duration: number;
  late_chunking_duration: number;
  embedding_duration: number;
  ingestion_duration: number;
  processing_duration: number;
  uri: string;
}

export interface UploadErrors {
  files: string;
  links: string;
}
