// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentNumberInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentInputValue } from "@/features/admin-panel/control-plane/types";

export const searchTypesArgsMap = {
  similarity: ["k"],
  similarity_distance_threshold: ["k", "distance_threshold"],
  // similarity_score_threshold: ["k", "score_threshold"],
  // mmr: ["k", "fetch_k", "lambda_mult"],
};

const searchTypes = Object.keys(searchTypesArgsMap);

export type RetrieverSearchType = keyof typeof searchTypesArgsMap;

export const retrieverFormConfig = {
  search_type: {
    name: "search_type",
    options: searchTypes,
  },
  k: {
    name: "k",
    range: { min: 1, max: 50 },
    tooltipText:
      "The number of nearest neighbors to retrieve from the database. It determines the size of the result set.",
  },
  distance_threshold: {
    name: "distance_threshold",
    range: { min: 0.1, max: 1 },
    nullable: true,
    tooltipText:
      "The maximum distance threshold for similarity search by vector. Documents with a distance greater than the threshold will not be considered as matches.",
  },
  fetch_k: {
    name: "fetch_k",
    range: { min: 10, max: 50 },
    tooltipText:
      "The number of additional documents to fetch for each retrieved document in max marginal relevance search.",
  },
  lambda_mult: {
    name: "lambda_mult",
    range: { min: 0.1, max: 1 },
    tooltipText:
      "A parameter that controls the trade-off between relevance and diversity in max marginal relevance search.",
  },
  score_threshold: {
    name: "score_threshold",
    range: { min: 0, max: 1 },
    tooltipText:
      "The minimum relevance score required for a document to be considered a match in similarity search with relevance scores.",
  },
};

export const retrieverArgumentsDefault: RetrieverArgs = {
  search_type: "similarity",
  k: null,
  distance_threshold: null,
  fetch_k: null,
  lambda_mult: null,
  score_threshold: null,
};

export interface RetrieverArgs
  extends Record<string, ServiceArgumentInputValue> {
  search_type: RetrieverSearchType;
  k: ServiceArgumentNumberInputValue;
  distance_threshold: ServiceArgumentNumberInputValue;
  fetch_k: ServiceArgumentNumberInputValue;
  lambda_mult: ServiceArgumentNumberInputValue;
  score_threshold: ServiceArgumentNumberInputValue;
}
