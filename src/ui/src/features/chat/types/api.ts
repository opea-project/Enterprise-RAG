// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FetchBaseQueryError } from "@reduxjs/toolkit/query";

import { ConversationTurn } from "@/types";

export interface PostPromptRequest {
  prompt: ConversationTurn["question"];
  conversationHistory?: Array<{
    question: ConversationTurn["question"];
    answer: ConversationTurn["answer"];
  }>;
  signal: AbortSignal;
  onAnswerUpdate: AnswerUpdateHandler;
}

export type AnswerUpdateHandler = (answer: ConversationTurn["answer"]) => void;

export type ChatErrorResponse = FetchBaseQueryError & {
  status: string | number;
  originalStatus?: number;
  data: unknown;
  error?: string;
};
