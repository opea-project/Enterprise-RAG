// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  banCompetitorsScanner,
  banSubstringsScanner,
  biasScanner,
  relevanceScanner,
} from "@/models/admin-panel/control-plane/guardrails/scanners";
import { GuardrailArguments } from "@/models/admin-panel/control-plane/serviceData";

export const outputGuardArguments: GuardrailArguments = {
  ban_competitors: banCompetitorsScanner,
  ban_substrings: banSubstringsScanner,
  bias: biasScanner,
  relevance: relevanceScanner,
};
