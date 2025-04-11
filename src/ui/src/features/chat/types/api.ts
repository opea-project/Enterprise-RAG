// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { UpdatedChatMessage } from "@/features/chat/types";

export enum HTTP_STATUS {
  REQUEST_TIMEOUT = 408,
  PAYLOAD_TOO_LARGE = 413,
  TOO_MANY_REQUESTS = 429,
  GUARDRAILS_ERROR = 466,
}

export type OnMessageTextUpdateHandler = (
  message: string | UpdatedChatMessage,
) => void;
