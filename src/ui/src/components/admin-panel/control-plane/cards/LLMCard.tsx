// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/components/admin-panel/control-plane/cards";
import SelectedServiceCard from "@/components/admin-panel/control-plane/SelectedServiceCard/SelectedServiceCard";
import ServiceArgumentCheckbox from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentNumberInput from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { LLMArgs, llmFormConfig } from "@/config/control-plane/llm";
import useServiceCard from "@/utils/hooks/useServiceCard";

const LLMCard = ({
  data: { id, status, displayName, llmArgs, details },
}: ControlPlaneCardProps) => {
  const {
    previousArgumentsValues,
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps,
  } = useServiceCard<LLMArgs>(id, llmArgs);

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      serviceDetails={details}
      footerProps={footerProps}
    >
      <p className="mb-1 mt-3 text-sm font-medium">Service Arguments</p>
      <ServiceArgumentNumberInput
        {...llmFormConfig.max_new_tokens}
        initialValue={previousArgumentsValues.max_new_tokens}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.top_k}
        initialValue={previousArgumentsValues.top_k}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.top_p}
        initialValue={previousArgumentsValues.top_p}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.typical_p}
        initialValue={previousArgumentsValues.typical_p}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.temperature}
        initialValue={previousArgumentsValues.temperature}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.repetition_penalty}
        initialValue={previousArgumentsValues.repetition_penalty}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentCheckbox
        {...llmFormConfig.streaming}
        initialValue={previousArgumentsValues.streaming}
        onArgumentValueChange={onArgumentValueChange}
      />
    </SelectedServiceCard>
  );
};

export default LLMCard;
