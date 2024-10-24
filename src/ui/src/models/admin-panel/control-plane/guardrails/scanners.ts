// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  CASE_SENSITIVE,
  COMPETITORS,
  CONTAINS_ALL,
  ENABLED,
  MATCH_TYPE,
  MODEL,
  REDACT,
  SUBSTRINGS,
  THRESHOLD,
  USE_ONNX,
  VALID_LANGUAGES,
} from "./arguments";

export const banCompetitorsScanner = [
  ENABLED,
  USE_ONNX,
  COMPETITORS,
  MODEL,
  REDACT,
  THRESHOLD,
];

export const banSubstringsScanner = [
  ENABLED,
  SUBSTRINGS,
  MATCH_TYPE,
  CASE_SENSITIVE,
  REDACT,
  CONTAINS_ALL,
];

export const biasScanner = [ENABLED, USE_ONNX, MODEL, THRESHOLD, MATCH_TYPE];

export const gibberishScanner = [
  ENABLED,
  USE_ONNX,
  MODEL,
  THRESHOLD,
  MATCH_TYPE,
];

export const languageScanner = [
  ENABLED,
  USE_ONNX,
  VALID_LANGUAGES,
  MODEL,
  THRESHOLD,
  MATCH_TYPE,
];

export const promptInjectionScanner = [
  ENABLED,
  USE_ONNX,
  MODEL,
  THRESHOLD,
  MATCH_TYPE,
];

export const relevanceScanner = [ENABLED, USE_ONNX, MODEL, THRESHOLD];
