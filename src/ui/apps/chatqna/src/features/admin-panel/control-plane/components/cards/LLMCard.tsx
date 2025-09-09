// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";
import ServiceArgumentCheckbox from "@/features/admin-panel/control-plane/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentNumberInput from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  LLMArgs,
  llmFormConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/llm";
import useServiceCard from "@/features/admin-panel/control-plane/hooks/useServiceCard";

const LLMCard = ({
  data: { id, status, displayName, llmArgs, details },
}: ControlPlaneCardProps) => {
  const {
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps,
    argumentsForm,
  } = useServiceCard<LLMArgs>(id, llmArgs);

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      serviceDetails={details}
      footerProps={footerProps}
    >
      <p className="mb-2 mt-3 text-sm font-medium">Service Arguments</p>
      <ServiceArgumentNumberInput
        {...llmFormConfig.max_new_tokens}
        value={argumentsForm.max_new_tokens}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.top_k}
        value={argumentsForm.top_k}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.top_p}
        value={argumentsForm.top_p}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.typical_p}
        value={argumentsForm.typical_p}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.temperature}
        value={argumentsForm.temperature}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...llmFormConfig.repetition_penalty}
        value={argumentsForm.repetition_penalty}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentCheckbox
        {...llmFormConfig.streaming}
        value={argumentsForm.streaming}
        onArgumentValueChange={onArgumentValueChange}
      />
    </SelectedServiceCard>
  );
};

export default LLMCard;
