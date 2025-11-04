// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Position } from "@xyflow/react";

export enum ServiceStatus {
  Ready = "Ready",
  NotReady = "Not ready",
  NotAvailable = "Status Not Available",
}

export interface ServiceNodeData extends Record<string, unknown> {
  id: string;
  displayName: string;
  targetPosition?: Position;
  sourcePosition?: Position;
  additionalTargetPosition?: Position;
  additionalTargetId?: string;
  additionalSourcePosition?: Position;
  additionalSourceId?: string;
  selected?: boolean;
  status?: ServiceStatus;
  configurable?: boolean;
}
