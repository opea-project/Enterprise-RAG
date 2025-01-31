// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  banCompetitorsScanner,
  banSubstringsScanner,
  codeScanner,
  gibberishScanner,
  languageScanner,
  promptInjectionScanner,
  regexScanner,
} from "@/models/admin-panel/control-plane/guardrails/scanners";
import { GuardrailArguments } from "@/models/admin-panel/control-plane/serviceData";

export const inputGuardArguments: GuardrailArguments = {
  prompt_injection: promptInjectionScanner,
  ban_substrings: banSubstringsScanner,
  code: codeScanner,
  regex: regexScanner,
  gibberish: gibberishScanner,
  language: languageScanner,
  ban_competitors: banCompetitorsScanner,
};
