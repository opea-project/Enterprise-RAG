// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  banCompetitorsScanner,
  BanCompetitorsScannerArgs,
  banSubstringsScanner,
  BanSubstringsScannerArgs,
  biasScanner,
  BiasScannerArgs,
  codeScanner,
  CodeScannerArgs,
  languageScanner,
  LanguageScannerArgs,
  maliciousUrlScanner,
  MaliciousURLsScannerArgs,
  relevanceScanner,
  RelevanceScannerArgs,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/scanners";
import { ServiceArgumentInputValue } from "@/features/admin-panel/control-plane/types";

export const llmOutputGuardFormConfig = {
  ban_substrings: banSubstringsScanner,
  code: codeScanner,
  bias: biasScanner,
  relevance: relevanceScanner,
  ban_competitors: banCompetitorsScanner,
  language: languageScanner,
  malicious_urls: maliciousUrlScanner,
};

export interface LLMOutputGuardArgs
  extends Record<string, Record<string, ServiceArgumentInputValue>> {
  ban_substrings: BanSubstringsScannerArgs;
  code: CodeScannerArgs;
  bias: BiasScannerArgs;
  relevance: RelevanceScannerArgs;
  ban_competitors: BanCompetitorsScannerArgs;
  language: LanguageScannerArgs;
  malicious_urls: MaliciousURLsScannerArgs;
}

export const llmOutputGuardArgumentsDefault: LLMOutputGuardArgs = {
  ban_substrings: {
    enabled: false,
    substrings: null,
    match_type: null,
    case_sensitive: false,
    redact: null,
    contains_all: null,
  },
  code: {
    enabled: false,
    threshold: null,
  },
  bias: {
    enabled: false,
    threshold: null,
    match_type: null,
  },
  relevance: {
    enabled: false,
    threshold: null,
  },
  ban_competitors: {
    enabled: false,
    competitors: null,
    redact: null,
    threshold: null,
  },
  language: {
    enabled: false,
    valid_languages: null,
    match_type: null,
    threshold: null,
  },
  malicious_urls: {
    enabled: false,
    threshold: null,
  },
};
