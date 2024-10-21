// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  banCompetitorsScanner,
  banSubstringsScanner,
  gibberishScanner,
  languageScanner,
  promptInjectionScanner,
} from "@/models/admin-panel/control-plane/guardrails/scanners";
import { GuardrailArguments } from "@/models/admin-panel/control-plane/serviceData";

export const inputGuardArguments: GuardrailArguments = {
  ban_competitors: banCompetitorsScanner,
  ban_substrings: banSubstringsScanner,
  gibberish: gibberishScanner,
  language: languageScanner,
  prompt_injection: promptInjectionScanner,
};
