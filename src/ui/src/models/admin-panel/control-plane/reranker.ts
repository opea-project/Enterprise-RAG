// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ServiceArgument from "@/models/admin-panel/control-plane/serviceArgument";

const SEARCH_TYPE: ServiceArgument = {
  displayName: "search_type",
  type: "text",
  value: null,
};

const K_PARAM: ServiceArgument = {
  displayName: "k",
  type: "number",
  range: { min: 1, max: 100 },
  value: null,
};

const DISTANCE_THRESHOLD: ServiceArgument = {
  displayName: "distance_threshold",
  type: "number",
  range: { min: 0.1, max: 1.0 },
  value: null,
  nullable: true,
};

const FETCH_K: ServiceArgument = {
  displayName: "fetch_k",
  type: "number",
  range: { min: 10, max: 100 },
  value: null,
};

const LAMBDA_MULT: ServiceArgument = {
  displayName: "lambda_mult",
  type: "number",
  range: { min: 0.1, max: 1.0 },
  value: null,
};

const SCORE_THRESHOLD: ServiceArgument = {
  displayName: "score_threshold",
  type: "number",
  range: { min: 0.0, max: 1.0 },
  value: null,
};

export const rerankerArguments = [
  SEARCH_TYPE,
  K_PARAM,
  DISTANCE_THRESHOLD,
  FETCH_K,
  LAMBDA_MULT,
  SCORE_THRESHOLD,
];
