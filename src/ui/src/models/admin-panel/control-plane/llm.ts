// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ServiceArgument from "@/models/admin-panel/control-plane/serviceArgument";

const MAX_NEW_TOKENS: ServiceArgument = {
  displayName: "max_new_tokens",
  type: "number",
  range: { min: 1, max: 2048 },
  value: null,
};

const TOP_K: ServiceArgument = {
  displayName: "top_k",
  type: "number",
  range: { min: 1, max: 50 },
  value: null,
};

const TOP_P: ServiceArgument = {
  displayName: "top_p",
  type: "number",
  range: { min: 0.5, max: 1.0 },
  value: null,
};

const TYPICAL_P: ServiceArgument = {
  displayName: "typical_p",
  type: "number",
  range: { min: 0.5, max: 1.0 },
  value: null,
};

const TEMPERATURE: ServiceArgument = {
  displayName: "temperature",
  type: "number",
  range: { min: 0.1, max: 1.0 },
  value: null,
};

const REPETITION_PENALTY: ServiceArgument = {
  displayName: "repetition_penalty",
  type: "number",
  range: { min: 1.0, max: 2.0 },
  value: null,
};

const STREAMING: ServiceArgument = {
  displayName: "streaming",
  type: "boolean",
  value: null,
};

export const llmArguments = [
  MAX_NEW_TOKENS,
  TOP_K,
  TOP_P,
  TYPICAL_P,
  TEMPERATURE,
  REPETITION_PENALTY,
  STREAMING,
];
