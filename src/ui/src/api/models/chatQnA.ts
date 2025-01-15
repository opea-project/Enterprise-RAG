// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { GuardrailParams } from "@/api/models/systemFingerprint";

export interface PromptRequestParams {
  [argName: string]:
    | string
    | number
    | boolean
    | GuardrailParams
    | null
    | undefined;
  input_guardrail_params?: GuardrailParams;
  output_guardrail_params?: GuardrailParams;
}
