// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface SummarizeResponse {
  summary: string;
}

export interface SummarizePlainTextRequest {
  text: string;
}

export interface SummarizeFileRequest {
  file: File;
}
