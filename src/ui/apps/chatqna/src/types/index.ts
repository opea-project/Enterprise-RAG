// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SourceDocumentType } from "@/features/chat/types";

export interface Chat {
  id: string;
  title: string;
  turns: ChatTurn[];
  inputValue: string;
}

// interface defined for chat elements displayed in UI
export interface ChatTurn {
  id: string;
  question: string;
  answer?: string;
  error: string | null;
  isPending: boolean;
  sources?: SourceDocumentType[];
}

export type AppEnvKey =
  | "API_URL"
  | "KEYCLOAK_URL"
  | "KEYCLOAK_REALM"
  | "KEYCLOAK_CLIENT_ID"
  | "ADMIN_RESOURCE_ROLE"
  | "GRAFANA_DASHBOARD_URL"
  | "KEYCLOAK_ADMIN_PANEL_URL"
  | "S3_URL"
  | "CHAT_DISCLAIMER_TEXT"
  | "ERAG_VERSION";
