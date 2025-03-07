// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentCheckboxValue } from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentNumberInputValue } from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentInputValue } from "@/types/admin-panel/control-plane";

export const llmFormConfig = {
  max_new_tokens: {
    name: "max_new_tokens",
    range: { min: 1, max: 2048 },
  },
  top_k: {
    name: "top_k",
    range: { min: 1, max: 50 },
  },
  top_p: {
    name: "top_p",
    range: { min: 0.5, max: 1 },
  },
  typical_p: {
    name: "typical_p",
    range: { min: 0.5, max: 1 },
  },
  temperature: {
    name: "temperature",
    range: { min: 0.1, max: 1 },
  },
  repetition_penalty: {
    name: "repetition_penalty",
    range: { min: 1, max: 2 },
  },
  streaming: {
    name: "streaming",
  },
};

export const llmArgumentsDefault: LLMArgs = {
  max_new_tokens: null,
  top_k: null,
  top_p: null,
  typical_p: null,
  temperature: null,
  repetition_penalty: null,
  streaming: true,
};

export interface LLMArgs extends Record<string, ServiceArgumentInputValue> {
  max_new_tokens: ServiceArgumentNumberInputValue;
  top_k: ServiceArgumentNumberInputValue;
  top_p: ServiceArgumentNumberInputValue;
  typical_p: ServiceArgumentNumberInputValue;
  temperature: ServiceArgumentNumberInputValue;
  repetition_penalty: ServiceArgumentNumberInputValue;
  streaming: ServiceArgumentCheckboxValue;
}
