// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ServiceArgument from "@/models/admin-panel/control-plane/serviceArgument";

const TOP_N: ServiceArgument = {
  displayName: "top_n",
  type: "number",
  range: { min: 1, max: 50 },
  value: null,
};

export const rerankerArguments = [TOP_N];
