// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface SummarizeResponse {
  id: string;
  json: string | null;
  text: string;
}

export type SummaryType = "map_reduce" | "stuff" | "refine";

export type SummaryUpdateHandler = (summaryChunk: string) => void;

export interface SummarizeRequest {
  onSummaryUpdate: SummaryUpdateHandler;
}

export interface SummarizePlainTextRequest extends SummarizeRequest {
  text: string;
  summaryType?: SummaryType;
}

export interface FileData {
  filename: string;
  data64: string;
  content_type: string;
}

export interface SummarizeFileRequest extends SummarizeRequest {
  fileData: FileData;
  summaryType?: SummaryType;
}
