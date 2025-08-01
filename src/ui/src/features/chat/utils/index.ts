// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { v4 as uuidv4 } from "uuid";

import { ChatHistoryEntry } from "@/features/chat/types/api";
import { ChatTurn } from "@/types";

export const createChatTurnsFromHistory = (
  history: ChatHistoryEntry[],
): ChatTurn[] =>
  history.map(({ question, answer }) => ({
    id: uuidv4(),
    question,
    answer,
    error: null,
    isPending: false,
  }));
