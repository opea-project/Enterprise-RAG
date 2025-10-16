// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface HistoryItemData {
  id: string;
  title: string; // filename or first 20 chars of plain text
  source: string; // filename or plain text
  sourceType?: "file" | "plainText";
  summary?: string;
  timestamp: string; // ISO string
}

export type AppEnvKey =
  | "API_URL"
  | "KEYCLOAK_URL"
  | "KEYCLOAK_REALM"
  | "KEYCLOAK_CLIENT_ID"
  | "ADMIN_RESOURCE_ROLE"
  | "GRAFANA_DASHBOARD_URL"
  | "KEYCLOAK_ADMIN_PANEL_URL";
