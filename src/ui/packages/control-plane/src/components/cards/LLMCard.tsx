// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SelectedServiceCard } from "@/components/SelectedServiceCard/SelectedServiceCard";
import { ServiceArgumentCheckbox } from "@/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentNumberInput } from "@/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentsTitle } from "@/components/ServiceArgumentsTitle/ServiceArgumentsTitle";
import { LLMArgs, llmFormConfig } from "@/configs/services/llm";
import { useServiceCard } from "@/hooks/useServiceCard";
import { ControlPlaneCardProps } from "@/types/cards";

export const LLMCard = ({
  data: { id, status, displayName, llmArgs, details },
  changeArguments,
}: ControlPlaneCardProps) => {
  const config = llmFormConfig;

  const {
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps,
    argumentsForm,
  } = useServiceCard<LLMArgs>(id, llmArgs, { changeArguments });

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      serviceDetails={details}
      footerProps={footerProps}
    >
      <ServiceArgumentsTitle>Service Arguments</ServiceArgumentsTitle>
      <ServiceArgumentNumberInput
        {...config.max_new_tokens}
        value={argumentsForm.max_new_tokens}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...config.top_k}
        value={argumentsForm.top_k}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...config.top_p}
        value={argumentsForm.top_p}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...config.typical_p}
        value={argumentsForm.typical_p}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...config.temperature}
        value={argumentsForm.temperature}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...config.repetition_penalty}
        value={argumentsForm.repetition_penalty}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentCheckbox
        {...config.stream}
        value={argumentsForm.stream}
        onArgumentValueChange={onArgumentValueChange}
      />
    </SelectedServiceCard>
  );
};
