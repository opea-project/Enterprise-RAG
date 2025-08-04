// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

type SourceType = "file" | "link";

interface Source {
  vector_distance: number;
  reranker_score: number;
  type: SourceType;
  citation_id: number;
}

export interface FileSource extends Source {
  type: "file";
  bucket_name: string;
  object_name: string;
}

export interface LinkSource extends Source {
  type: "link";
  url: string;
}

export type SourceDocumentType = FileSource | LinkSource;
