// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FetchBaseQueryError } from "@reduxjs/toolkit/query";

import { ChatTurn, SourceDocumentType } from "@/types";

// type for history array that is sent to API via POST request on /save endpoint
export interface ChatHistoryEntry {
  question: string;
  answer?: string;
  metadata?: {
    reranked_docs?: SourceDocumentType[];
  };
  timestamp?: string | null;
}

export interface PostPromptRequest {
  prompt: string;
  id?: string;
  signal: AbortSignal;
  onAnswerUpdate: AnswerUpdateHandler;
  onSourcesUpdate: SourcesUpdateHandler;
}

export type AnswerUpdateHandler = (answer: ChatTurn["answer"]) => void;

export type SourcesUpdateHandler = (sources: SourceDocumentType[]) => void;

export type ChatErrorResponse = FetchBaseQueryError & {
  status: string | number;
  originalStatus?: number;
  data: unknown;
  error?: string;
};

export interface ApiChatItemData {
  history_name: string;
  id: string;
}

export interface ChatHistoryItemData {
  id: string;
  name: string;
  isPinned?: boolean;
}

export interface SaveChatRequest {
  history: ChatHistoryEntry[];
  id?: string; // if not provided, a new history will be created
}

export type SaveChatResponse = ChatHistoryItemData;

export type GetAllChatsResponse = ChatHistoryItemData[];

export interface GetChatByIdResponse {
  historyId: string;
  history: ChatHistoryEntry[];
  historyName: string;
}

export interface GetChatByIdRequest {
  id: string;
}

export interface ChangeChatNameRequest {
  id: string;
  newName: string;
}

export interface DeleteChatRequest {
  id: string;
}
