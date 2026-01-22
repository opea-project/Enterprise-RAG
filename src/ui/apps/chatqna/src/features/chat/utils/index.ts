// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { v4 as uuidv4 } from "uuid";

import { SourceDocumentType } from "@/features/chat/types";
import { ChatHistoryEntry } from "@/features/chat/types/api";
import { ChatTurn } from "@/types";

export const createChatTurnsFromHistory = (
  history: ChatHistoryEntry[],
): ChatTurn[] =>
  history.map(({ question, answer, metadata }) => {
    const sources = metadata?.reranked_docs ?? [];
    const parsedSources = parseSources(sources);
    return {
      id: uuidv4(),
      question,
      answer,
      error: null,
      isPending: false,
      sources: parsedSources.length > 0 ? parsedSources : [],
    };
  });

export const parseSources = (sources: SourceDocumentType[]) =>
  sources.reduce((parsedSources, source) => {
    const existingSource = parsedSources.find(
      (s) => s.citation_id === source.citation_id,
    );
    if (existingSource) {
      if (!existingSource.citations) {
        existingSource.citations = [];
      }
      if (source.text) {
        existingSource.citations.push(source.text);
      }
    } else {
      if (!source.text) {
        parsedSources.push(source);
        return parsedSources;
      }
      parsedSources.push({ ...source, citations: [source.text] });
    }
    return parsedSources;
  }, [] as SourceDocumentType[]);
