// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface ConversationTurn {
  id: string;
  question: string;
  answer: string;
  error: string | null;
  isPending: boolean;
}
