// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentCheckboxValue } from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentNumberInputValue } from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentTextInputValue } from "@/components/admin-panel/control-plane/ServiceArgumentTextInput/ServiceArgumentTextInput";
import { ThreeStateSwitchValue } from "@/components/shared/ThreeStateSwitch/ThreeStateSwitch";
import { ServiceArgumentInputValue } from "@/types/admin-panel/control-plane";

import {
  caseSensitive,
  competitors,
  containsAll,
  enabled,
  matchType,
  patterns,
  redact,
  substrings,
  threshold,
  validLanguages,
} from "./arguments";

export const banCompetitorsScanner = {
  enabled,
  competitors,
  redact,
  threshold,
};

export const banSubstringsScanner = {
  enabled,
  substrings,
  match_type: matchType,
  case_sensitive: caseSensitive,
  redact,
  contains_all: containsAll,
};

export const biasScanner = {
  enabled,
  threshold,
  match_type: matchType,
};

export const gibberishScanner = {
  enabled,
  threshold,
  match_type: matchType,
};

export const languageScanner = {
  enabled,
  valid_languages: validLanguages,
  threshold,
  match_type: matchType,
};

export const promptInjectionScanner = {
  enabled,
  threshold,
  match_type: matchType,
};

export const relevanceScanner = { enabled, threshold };

export const codeScanner = { enabled, threshold };

export const regexScanner = {
  enabled,
  patterns,
  match_type: matchType,
  redact,
};

export const maliciousUrlScanner = { enabled, threshold };

export interface BanSubstringsScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  substrings: ServiceArgumentTextInputValue;
  match_type: ServiceArgumentTextInputValue;
  case_sensitive: ServiceArgumentCheckboxValue;
  redact: ThreeStateSwitchValue;
  contains_all: ThreeStateSwitchValue;
}

export interface CodeScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
}

export interface BiasScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
  match_type: ServiceArgumentTextInputValue;
}

export interface RelevanceScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
}

export interface BanCompetitorsScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  competitors: ServiceArgumentTextInputValue;
  redact: ThreeStateSwitchValue;
  threshold: ServiceArgumentNumberInputValue;
}

export interface LanguageScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  valid_languages: ServiceArgumentTextInputValue;
  threshold: ServiceArgumentNumberInputValue;
  match_type: ServiceArgumentTextInputValue;
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
  match_type: ServiceArgumentTextInputValue;
}

export interface RegexScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  patterns: ServiceArgumentTextInputValue;
  match_type: ServiceArgumentTextInputValue;
  redact: ThreeStateSwitchValue;
}

export interface GibberishScannerArgs
  extends Record<string, ServiceArgumentInputValue> {
  enabled: ServiceArgumentCheckboxValue;
  threshold: ServiceArgumentNumberInputValue;
  match_type: ServiceArgumentTextInputValue;
}

export type BanCompetitorsScannerConfig = typeof banCompetitorsScanner;
export type BanSubstringsScannerConfig = typeof banSubstringsScanner;
export type BiasScannerConfig = typeof biasScanner;
export type GibberishScannerConfig = typeof gibberishScanner;
export type LanguageScannerConfig = typeof languageScanner;
export type PromptInjectionScannerConfig = typeof promptInjectionScanner;
export type RelevanceScannerConfig = typeof relevanceScanner;
export type CodeScannerConfig = typeof codeScanner;
export type RegexScannerConfig = typeof regexScanner;
export type MaliciousURLsScannerConfig = typeof maliciousUrlScanner;
