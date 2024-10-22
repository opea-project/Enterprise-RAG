// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Position } from "@xyflow/react";

import ServiceArgument from "@/models/admin-panel/control-plane/serviceArgument";

export interface GuardrailArguments {
  [scannerName: string]: ServiceArgument[];
}

export interface ServiceDetails {
  [key: string]: string | boolean | number;
}

export enum ServiceStatus {
  Ready = "Ready",
  NotReady = "Not ready",
  NotAvailable = "Status Not Available",
}

export interface ServiceData extends Record<string, unknown> {
  id: string;
  displayName: string;
  args?: ServiceArgument[];
  guardArgs?: GuardrailArguments;
  details?: ServiceDetails;
  targetPosition?: Position;
  sourcePosition?: Position;
  additionalTargetPosition?: Position;
  additionalTargetId?: string;
  additionalSourcePosition?: Position;
  additionalSourceId?: string;
  selected?: boolean;
  status?: ServiceStatus;
}
