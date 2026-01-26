// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface ChatTurn {
  id: string;
  question: string;
  answer?: string;
  error: string | null;
  isPending: boolean;
  sources?: SourceDocumentType[];
}

export interface Chat {
  id: string;
  title: string;
  turns: ChatTurn[];
  inputValue: string;
}

type SourceType = "file" | "link";

interface Source {
  vector_distance: number;
  reranker_score: number;
  type: SourceType;
  citation_id: number;
  text?: string;
  citations?: string[];
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

export interface ChatHistoryItemData {
  name: string;
  id: string;
}
