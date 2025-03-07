// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const enabled = {
  name: "enabled",
};

export const useOnnx = {
  name: "use_onnx",
};

export const model = {
  name: "model",
  nullable: true,
};

export const threshold = {
  name: "threshold",
  nullable: true,
  range: { min: 0, max: 1 },
};

export const matchType = {
  name: "match_type",
  nullable: true,
};

export const competitors = {
  name: "competitors",
  commaSeparated: true,
};

export const substrings = {
  name: "substrings",
  commaSeparated: true,
};

export const caseSensitive = {
  name: "case_sensitive",
};

export const redact = {
  name: "redact",
};

export const containsAll = {
  name: "contains_all",
};

export const validLanguages = {
  name: "valid_languages",
  commaSeparated: true,
};

export const patterns = {
  name: "patterns",
  commaSeparated: true,
};
