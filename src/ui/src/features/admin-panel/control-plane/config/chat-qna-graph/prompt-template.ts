// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentTextAreaValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentTextArea/ServiceArgumentTextArea";
import { ServiceArgumentInputValue } from "@/features/admin-panel/control-plane/types";

export const promptTemplateFormConfig = {
  user_prompt_template: {
    name: "user_prompt_template",
    tooltipText:
      "Instructions provided by an end user and placeholders for any user input",
  },
  system_prompt_template: {
    name: "system_prompt_template",
    tooltipText:
      "System's rules and business logic, like a function definition, and placeholders for any generated content",
  },
};

export interface PromptTemplateArgs
  extends Record<string, ServiceArgumentInputValue> {
  user_prompt_template: ServiceArgumentTextAreaValue;
  system_prompt_template: ServiceArgumentTextAreaValue;
}

export const promptTemplateArgumentsDefault: PromptTemplateArgs = {
  user_prompt_template: "",
  system_prompt_template: "",
};
