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
  isNullable: true,
};

export const threshold = {
  name: "threshold",
  isNullable: true,
  range: { min: 0, max: 1 },
};

export const matchType = {
  name: "match_type",
  isNullable: true,
};

export const competitors = {
  name: "competitors",
  isCommaSeparated: true,
};

export const substrings = {
  name: "substrings",
  isCommaSeparated: true,
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
  isCommaSeparated: true,
};

export const patterns = {
  name: "patterns",
  isCommaSeparated: true,
};
