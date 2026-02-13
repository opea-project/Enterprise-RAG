// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  banSubstringsScanner,
  BanSubstringsScannerArgs,
  biasScanner,
  BiasScannerArgs,
  codeScanner,
  CodeScannerArgs,
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
  malicious_urls: maliciousUrlScanner,
};

export interface LLMOutputGuardArgs
  extends Record<string, Record<string, ServiceArgumentInputValue>> {
  ban_substrings: BanSubstringsScannerArgs;
  code: CodeScannerArgs;
  bias: BiasScannerArgs;
  relevance: RelevanceScannerArgs;
  malicious_urls: MaliciousURLsScannerArgs;
}

export const llmOutputGuardArgumentsDefault: LLMOutputGuardArgs = {
  ban_substrings: {
    enabled: false,
    substrings: null,
    match_type: "str",
    case_sensitive: false,
    redact: false,
    contains_all: false,
  },
  code: {
    enabled: false,
    threshold: null,
    languages: null,
  },
  bias: {
    enabled: false,
    threshold: null,
    match_type: "full",
  },
  relevance: {
    enabled: false,
    threshold: null,
  },
  malicious_urls: {
    enabled: false,
    threshold: null,
  },
};
