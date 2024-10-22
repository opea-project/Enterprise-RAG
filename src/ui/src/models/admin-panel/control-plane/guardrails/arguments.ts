// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ServiceArgument from "@/models/admin-panel/control-plane/serviceArgument";

export const ENABLED: ServiceArgument = {
  displayName: "enabled",
  type: "boolean",
  value: false,
};

export const USE_ONNX: ServiceArgument = {
  displayName: "use_onnx",
  type: "boolean",
  value: true,
};

export const MODEL: ServiceArgument = {
  displayName: "model",
  type: "text",
  value: null,
  nullable: true,
};

export const THRESHOLD: ServiceArgument = {
  displayName: "threshold",
  type: "number",
  value: null,
  nullable: true,
  range: { min: 0, max: 1.0 },
};

export const MATCH_TYPE: ServiceArgument = {
  displayName: "match_type",
  type: "text",
  value: null,
  nullable: true,
};

export const COMPETITORS: ServiceArgument = {
  displayName: "competitors",
  type: "text",
  value: null,
  commaSeparated: true,
};

export const SUBSTRINGS: ServiceArgument = {
  displayName: "substrings",
  type: "text",
  value: null,
  commaSeparated: true,
};

export const CASE_SENSITIVE: ServiceArgument = {
  displayName: "case_sensitive",
  type: "boolean",
  value: false,
};

export const REDACT: ServiceArgument = {
  displayName: "redact",
  type: "boolean",
  value: null,
  nullable: true,
};

export const CONTAINS_ALL: ServiceArgument = {
  displayName: "contains_all",
  type: "boolean",
  value: null,
  nullable: true,
};

export const VALID_LANGUAGES: ServiceArgument = {
  displayName: "valid_languages",
  type: "text",
  value: null,
  commaSeparated: true,
};
