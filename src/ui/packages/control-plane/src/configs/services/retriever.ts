// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ServiceArgumentInputValue,
  ServiceArgumentNumberInputValue,
} from "@/types/index";

export const metadataExtractionModes = ["off", "regex_only"] as const;
export const metadataExtractionModesWithNer = [
  "off",
  "regex_only",
  "hybrid",
  "ner_only",
] as const;

export type MetadataExtractionMode =
  (typeof metadataExtractionModesWithNer)[number];

export const searchTypesArgsMap = {
  similarity: ["k"],
  similarity_search_with_siblings: ["k", "distance_threshold"],
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
    isNullable: true,
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
  metadata_extraction_mode: {
    name: "metadata_extraction_mode",
    options: [...metadataExtractionModes],
    tooltipText:
      "Controls how metadata is extracted from queries for filtering. 'off' disables metadata filtering (default), 'regex_only' uses pattern matching to extract authors, dates, and titles. 'hybrid' uses both regex and NER, 'ner_only' uses the NER model only. Hybrid and NER modes require the OVMS NER model server.",
  },
};

export const retrieverArgumentsDefault: RetrieverArgs = {
  search_type: "similarity",
  k: null,
  distance_threshold: null,
  fetch_k: null,
  lambda_mult: null,
  score_threshold: null,
  metadata_extraction_mode: "off",
};

export interface RetrieverArgs extends Record<
  string,
  ServiceArgumentInputValue
> {
  search_type: RetrieverSearchType;
  k: ServiceArgumentNumberInputValue;
  distance_threshold: ServiceArgumentNumberInputValue;
  fetch_k: ServiceArgumentNumberInputValue;
  lambda_mult: ServiceArgumentNumberInputValue;
  score_threshold: ServiceArgumentNumberInputValue;
  metadata_extraction_mode: MetadataExtractionMode;
}
