// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { v4 as uuidv4 } from "uuid";

import { SourceDocumentType } from "@/features/chat/types";
import { ChatHistoryEntry } from "@/features/chat/types/api";
import { ChatTurn } from "@/types";

export const createChatTurnsFromHistory = (
  history: ChatHistoryEntry[],
): ChatTurn[] =>
  history.map(({ question, answer, metadata }) => ({
    id: uuidv4(),
    question,
    answer,
    error: null,
    isPending: false,
    sources: metadata?.reranked_docs ?? [],
  }));

export const createUniqueSources = (sources: SourceDocumentType[]) =>
  Array.from(
    new Map(
      sources
        .filter((src) => src.citation_id)
        .map((src) => [src.citation_id, src]),
    ).values(),
  );
