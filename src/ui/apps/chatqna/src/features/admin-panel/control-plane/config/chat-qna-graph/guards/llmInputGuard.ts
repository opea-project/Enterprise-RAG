// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  banSubstringsScanner,
  BanSubstringsScannerArgs,
  banTopicsScanner,
  BanTopicsScannerArgs,
  codeScanner,
  CodeScannerArgs,
  invisibleTextScanner,
  InvisibleTextScannerArgs,
  promptInjectionScanner,
  PromptInjectionScannerArgs,
  regexScanner,
  RegexScannerArgs,
  secretsScanner,
  SecretsScannerArgs,
  sentimentScanner,
  SentimentScannerArgs,
  tokenLimitScanner,
  TokenLimitScannerArgs,
  toxicityScanner,
  ToxicityScannerArgs,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/scanners";
import { ServiceArgumentInputValue } from "@/features/admin-panel/control-plane/types";

export const llmInputGuardFormConfig = {
  prompt_injection: promptInjectionScanner,
  ban_substrings: banSubstringsScanner,
  code: codeScanner,
  invisible_text: invisibleTextScanner,
  regex: regexScanner,
  ban_topics: banTopicsScanner,
  secrets: secretsScanner,
  sentiment: sentimentScanner,
  token_limit: tokenLimitScanner,
  toxicity: toxicityScanner,
};

export interface LLMInputGuardArgs
  extends Record<string, Record<string, ServiceArgumentInputValue>> {
  prompt_injection: PromptInjectionScannerArgs;
  ban_substrings: BanSubstringsScannerArgs;
  code: CodeScannerArgs;
  invisible_text: InvisibleTextScannerArgs;
  regex: RegexScannerArgs;
  ban_topics: BanTopicsScannerArgs;
  secrets: SecretsScannerArgs;
  sentiment: SentimentScannerArgs;
  token_limit: TokenLimitScannerArgs;
  toxicity: ToxicityScannerArgs;
}

export const llmInputGuardArgumentsDefault: LLMInputGuardArgs = {
  prompt_injection: {
    enabled: false,
    threshold: null,
    match_type: "full",
  },
  ban_substrings: {
    enabled: false,
    substrings: null,
    match_type: "str",
    case_sensitive: false,
    redact: null,
    contains_all: null,
  },
  code: {
    enabled: false,
    threshold: null,
    languages: null,
  },
  invisible_text: {
    enabled: false,
  },
  regex: {
    enabled: false,
    patterns: null,
    match_type: "all",
    redact: null,
  },
  ban_topics: {
    enabled: false,
    topics: null,
    threshold: null,
  },
  secrets: {
    enabled: false,
    redact_mode: "all",
  },
  sentiment: {
    enabled: false,
    threshold: null,
  },
  token_limit: {
    enabled: false,
    limit: null,
  },
  toxicity: {
    enabled: false,
    threshold: null,
    match_type: "full",
  },
};
