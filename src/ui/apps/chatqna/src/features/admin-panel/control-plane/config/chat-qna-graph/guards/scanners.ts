// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentCheckboxValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentNumberInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentSelectInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import { ServiceArgumentTextInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentTextInput/ServiceArgumentTextInput";
import {
  caseSensitive,
  containsAll,
  enabled,
  languages,
  limit,
  matchType,
  patterns,
  redact,
  redactMode,
  substrings,
  threshold,
  topics,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/arguments";
import { ServiceArgumentInputValue } from "@/features/admin-panel/control-plane/types";

export const banSubstringsScanner = {
  enabled,
  substrings,
  match_type: matchType(["str", "word"]),
  case_sensitive: caseSensitive,
  redact,
  contains_all: containsAll,
};

export const biasScanner = {
  enabled,
  threshold,
  match_type: matchType(["sentence", "full"]),
};

export const promptInjectionScanner = {
  enabled,
  threshold,
  match_type: matchType([
    "sentence",
    "full",
    "truncate_token_head_tail",
    "truncate_head_tail",
    "chunks",
  ]),
};

export const relevanceScanner = { enabled, threshold };

export const codeScanner = { enabled, threshold, languages };

export const invisibleTextScanner = { enabled };

export const regexScanner = {
  enabled,
  patterns,
  match_type: matchType(["search", "fullmatch", "all"]),
  redact,
};

export const maliciousUrlScanner = { enabled, threshold };

export const banTopicsScanner = { enabled, threshold, topics };

export const secretsScanner = {
  enabled,
  redact_mode: redactMode(["partial", "all", "hash"]),
};

export const sentimentScanner = {
  enabled,
  threshold: {
    ...threshold,
    range: { min: -1, max: 1 },
  },
};

export const tokenLimitScanner = { enabled, limit };

export const toxicityScanner = {
  enabled,
  threshold,
  match_type: matchType(["sentence", "full"]),
};

export interface BanSubstringsScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  substrings: ServiceArgumentTextInputValue;
  match_type: ServiceArgumentSelectInputValue;
  case_sensitive: ServiceArgumentCheckboxValue;
  redact: ServiceArgumentCheckboxValue;
  contains_all: ServiceArgumentCheckboxValue;
}

export interface CodeScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
  languages: ServiceArgumentTextInputValue;
}

export interface InvisibleTextScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
}

export interface InvisibleTextScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
}

export interface BiasScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
  match_type: ServiceArgumentSelectInputValue;
}

export interface RelevanceScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
}

export interface MaliciousURLsScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
}

export interface PromptInjectionScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
  match_type: ServiceArgumentSelectInputValue;
}

export interface RegexScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  patterns: ServiceArgumentTextInputValue;
  match_type: ServiceArgumentSelectInputValue;
  redact: ServiceArgumentCheckboxValue;
}

export interface BanTopicsScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  topics: ServiceArgumentTextInputValue;
  threshold: ServiceArgumentNumberInputValue;
}

export interface SecretsScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  redact_mode: ServiceArgumentSelectInputValue;
}

export interface SentimentScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
}

export interface TokenLimitScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  limit: ServiceArgumentNumberInputValue;
}

export interface ToxicityScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
  match_type: ServiceArgumentSelectInputValue;
}

export type BanSubstringsScannerConfig = typeof banSubstringsScanner;
export type BiasScannerConfig = typeof biasScanner;
export type PromptInjectionScannerConfig = typeof promptInjectionScanner;
export type RelevanceScannerConfig = typeof relevanceScanner;
export type CodeScannerConfig = typeof codeScanner;
export type InvisibleTextScannerConfig = typeof invisibleTextScanner;
export type RegexScannerConfig = typeof regexScanner;
export type MaliciousURLsScannerConfig = typeof maliciousUrlScanner;
export type BanTopicsScannerConfig = typeof banTopicsScanner;
export type SecretsScannerConfig = typeof secretsScanner;
export type SentimentScannerConfig = typeof sentimentScanner;
export type TokenLimitScannerConfig = typeof tokenLimitScanner;
export type ToxicityScannerConfig = typeof toxicityScanner;
