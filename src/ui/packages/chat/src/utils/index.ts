// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { v4 as uuidv4 } from "uuid";

import { ChatTurn, SourceDocumentType } from "@/types";
import { ChatHistoryEntry } from "@/types/api";

/**
 * Parses and consolidates source documents by grouping citations with the same citation_id.
 * If multiple sources share the same citation_id, their text values are merged into a citations array.
 *
 * @param sources - Array of source documents to parse
 * @returns Consolidated array of source documents with grouped citations
 */
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

/**
 * Converts chat history entries from the API into chat turn objects.
 * Each history entry is transformed into a ChatTurn with parsed sources and a unique ID.
 *
 * @param history - Array of chat history entries from the API
 * @returns Array of chat turn objects with parsed sources
 */
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
