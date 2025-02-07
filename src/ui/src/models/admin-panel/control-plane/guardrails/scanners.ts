// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  CASE_SENSITIVE,
  COMPETITORS,
  CONTAINS_ALL,
  ENABLED,
  MATCH_TYPE,
  PATTERNS,
  REDACT,
  SUBSTRINGS,
  THRESHOLD,
  VALID_LANGUAGES,
} from "./arguments";

export const banCompetitorsScanner = [ENABLED, COMPETITORS, REDACT, THRESHOLD];

export const banSubstringsScanner = [
  ENABLED,
  SUBSTRINGS,
  MATCH_TYPE,
  CASE_SENSITIVE,
  REDACT,
  CONTAINS_ALL,
];

export const biasScanner = [ENABLED, THRESHOLD, MATCH_TYPE];

export const gibberishScanner = [ENABLED, THRESHOLD, MATCH_TYPE];

export const languageScanner = [
  ENABLED,
  VALID_LANGUAGES,
  THRESHOLD,
  MATCH_TYPE,
];

export const promptInjectionScanner = [ENABLED, THRESHOLD, MATCH_TYPE];

export const relevanceScanner = [ENABLED, THRESHOLD];

export const codeScanner = [ENABLED, THRESHOLD];

export const regexScanner = [ENABLED, PATTERNS, MATCH_TYPE, REDACT];

export const maliciousUrlScanner = [ENABLED, THRESHOLD];
