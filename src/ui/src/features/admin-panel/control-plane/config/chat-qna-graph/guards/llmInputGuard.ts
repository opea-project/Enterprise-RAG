// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  banCompetitorsScanner,
  BanCompetitorsScannerArgs,
  banSubstringsScanner,
  BanSubstringsScannerArgs,
  codeScanner,
  CodeScannerArgs,
  gibberishScanner,
  GibberishScannerArgs,
  languageScanner,
  LanguageScannerArgs,
  promptInjectionScanner,
  PromptInjectionScannerArgs,
  regexScanner,
  RegexScannerArgs,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/scanners";
import { ServiceArgumentInputValue } from "@/features/admin-panel/control-plane/types";

export const llmInputGuardFormConfig = {
  prompt_injection: promptInjectionScanner,
  ban_substrings: banSubstringsScanner,
  code: codeScanner,
  regex: regexScanner,
  gibberish: gibberishScanner,
  language: languageScanner,
  ban_competitors: banCompetitorsScanner,
};

export interface LLMInputGuardArgs
  extends Record<string, Record<string, ServiceArgumentInputValue>> {
  prompt_injection: PromptInjectionScannerArgs;
  ban_substrings: BanSubstringsScannerArgs;
  code: CodeScannerArgs;
  regex: RegexScannerArgs;
  gibberish: GibberishScannerArgs;
  language: LanguageScannerArgs;
  ban_competitors: BanCompetitorsScannerArgs;
}

export const llmInputGuardArgumentsDefault: LLMInputGuardArgs = {
  prompt_injection: {
    enabled: false,
    threshold: null,
    match_type: null,
  },
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
  regex: {
    enabled: false,
    patterns: null,
    match_type: null,
    redact: null,
  },
  gibberish: {
    enabled: false,
    threshold: null,
    match_type: null,
  },
  language: {
    enabled: false,
    valid_languages: null,
    match_type: null,
    threshold: null,
  },
  ban_competitors: {
    enabled: false,
    competitors: null,
    redact: null,
    threshold: null,
  },
};
