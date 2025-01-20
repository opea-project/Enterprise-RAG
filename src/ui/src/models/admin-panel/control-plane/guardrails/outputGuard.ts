// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  banCompetitorsScanner,
  banSubstringsScanner,
  biasScanner,
  relevanceScanner,
  languageScanner,
  maliciousUrlScanner,
  codeScanner,
} from "@/models/admin-panel/control-plane/guardrails/scanners";
import { GuardrailArguments } from "@/models/admin-panel/control-plane/serviceData";

export const outputGuardArguments: GuardrailArguments = {
  ban_substrings: banSubstringsScanner,
  code: codeScanner,
  bias: biasScanner,
  relevance: relevanceScanner,
  ban_competitors: banCompetitorsScanner,
  language: languageScanner,
  malicious_urls: maliciousUrlScanner,
};
