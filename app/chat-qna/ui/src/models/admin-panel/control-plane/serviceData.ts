// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Position } from "@xyflow/react";

import ServiceArgument from "@/models/admin-panel/control-plane/serviceArgument";
import { ServiceStatus } from "@/models/admin-panel/control-plane/serviceStatus";

export interface ServiceData extends Record<string, unknown> {
  id: string;
  displayName: string;
  args?: ServiceArgument[];
  details?: { [key: string]: string | boolean | number };
  targetPosition?: Position;
  sourcePosition?: Position;
  additionalTargetPosition?: Position;
  additionalTargetId?: string;
  selected?: boolean;
  status: ServiceStatus;
}
