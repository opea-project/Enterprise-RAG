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

export const matchType = (options?: string[]) => ({
  name: "match_type",
  isNullable: true,
  options: options || [],
});

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

export const topics = {
  name: "topics",
  isCommaSeparated: true,
};

export const redactMode = (options?: string[]) => ({
  name: "redact_mode",
  isNullable: true,
  options: options || [],
});

export const limit = {
  name: "limit",
  isNullable: true,
  range: { min: 0, max: 1000000000 },
};

export const languages = {
  name: "languages",
  isCommaSeparated: true,
};
