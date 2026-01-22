// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface Notification {
  id: string;
  text: string;
  severity: NotificationSeverity;
}

export type NotificationSeverity = "success" | "error";
