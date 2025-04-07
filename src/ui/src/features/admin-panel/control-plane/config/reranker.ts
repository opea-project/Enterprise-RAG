// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentNumberInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentInputValue } from "@/features/admin-panel/control-plane/types";

export const rerankerFormConfig = {
  top_n: {
    name: "top_n",
    range: { min: 1, max: 50 },
  },
  rerank_score_threshold: {
    name: "rerank_score_threshold",
    range: { min: 0.0, max: 1.0 },
    tooltipText:
      "Reranking model returns a similarity distance that is mapped to a float value between 0 and 1 using a sigmoid function. With these parameters you can filter received docs. If rerank_score_threshold is defined, the microservice will ignore all chunks that returned a score equal or lower than this value.",
  },
};

export interface RerankerArgs
  extends Record<string, ServiceArgumentInputValue> {
  top_n: ServiceArgumentNumberInputValue;
  rerank_score_threshold: ServiceArgumentNumberInputValue;
}

export const rerankerArgumentsDefault: RerankerArgs = { top_n: undefined, rerank_score_threshold: undefined };
