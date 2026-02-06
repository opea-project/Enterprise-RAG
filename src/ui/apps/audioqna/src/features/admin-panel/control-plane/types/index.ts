// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceNodeData } from "@intel-enterprise-rag-ui/control-plane";

export interface ServiceDetails {
  [key: string]: string | boolean | number;
}

export interface ServiceData extends ServiceNodeData {
  details?: ServiceDetails;
}
