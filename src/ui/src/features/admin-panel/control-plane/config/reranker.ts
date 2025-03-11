// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentNumberInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentInputValue } from "@/features/admin-panel/control-plane/types";

export const rerankerFormConfig = {
  top_n: {
    name: "top_n",
    range: { min: 1, max: 50 },
  },
};

export interface RerankerArgs
  extends Record<string, ServiceArgumentInputValue> {
  top_n: ServiceArgumentNumberInputValue;
}

export const rerankerArgumentsDefault: RerankerArgs = { top_n: undefined };
