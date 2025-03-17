// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface ChatMessage {
  text: string;
  id: string;
  isUserMessage: boolean;
  isStreaming?: boolean;
  isError?: boolean;
}
