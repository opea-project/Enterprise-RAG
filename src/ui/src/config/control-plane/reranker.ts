// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentNumberInputValue } from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentInputValue } from "@/types/admin-panel/control-plane";

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
