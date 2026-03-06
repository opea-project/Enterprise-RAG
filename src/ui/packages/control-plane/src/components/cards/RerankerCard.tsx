// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SelectedServiceCard } from "@/components/SelectedServiceCard/SelectedServiceCard";
import { ServiceArgumentNumberInput } from "@/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentsTitle } from "@/components/ServiceArgumentsTitle/ServiceArgumentsTitle";
import { RerankerArgs, rerankerFormConfig } from "@/configs/services/reranker";
import { useServiceCard } from "@/hooks/useServiceCard";
import { ControlPlaneCardProps } from "@/types/cards";

export const RerankerCard = ({
  data: { id, status, details, displayName, rerankerArgs },
  changeArguments,
}: ControlPlaneCardProps) => {
  const config = rerankerFormConfig;

  const {
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps,
    argumentsForm,
  } = useServiceCard<RerankerArgs>(id, rerankerArgs, { changeArguments });

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      serviceDetails={details}
      footerProps={footerProps}
    >
      <ServiceArgumentsTitle>Service Arguments</ServiceArgumentsTitle>
      <ServiceArgumentNumberInput
        {...config.top_n}
        value={argumentsForm.top_n}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...config.rerank_score_threshold}
        value={argumentsForm.rerank_score_threshold}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
    </SelectedServiceCard>
  );
};
