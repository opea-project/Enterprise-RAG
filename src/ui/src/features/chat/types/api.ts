// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FetchBaseQueryError } from "@reduxjs/toolkit/query";

import { SourceDocumentType } from "@/features/chat/types";
import { ChatTurn } from "@/types";

// type for history array that is sent to API via POST request on /save endpoint
export interface ChatHistoryEntry {
  question: string;
  answer?: string;
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

export interface APIChatItemData {
  history_name: string;
  id: string;
}

export interface ChatItemData {
  name: string;
  id: string;
}

export interface SaveChatRequest {
  history: ChatHistoryEntry[];
  id?: string; // if not provided, a new history will be created
}

export type SaveChatResponse = ChatItemData;

export type GetAllChatsResponse = ChatItemData[];

export interface APIGetChatByIdResponse {
  _id: string;
  history: ChatHistoryEntry[];
  user_id: string;
  history_name: string;
}

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
