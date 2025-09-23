// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";
import ServiceArgumentNumberInput from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  RerankerArgs,
  rerankerFormConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/reranker";
import useServiceCard from "@/features/admin-panel/control-plane/hooks/useServiceCard";

const RerankerCard = ({
  data: { id, status, details, displayName, rerankerArgs },
}: ControlPlaneCardProps) => {
  const {
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps,
    argumentsForm,
  } = useServiceCard<RerankerArgs>(id, rerankerArgs);

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      serviceDetails={details}
      footerProps={footerProps}
    >
      <p className="mb-2 mt-3 text-sm font-medium">Service Arguments</p>
      <ServiceArgumentNumberInput
        {...rerankerFormConfig.top_n}
        value={argumentsForm.top_n}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...rerankerFormConfig.rerank_score_threshold}
        value={argumentsForm.rerank_score_threshold}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
    </SelectedServiceCard>
  );
};

export default RerankerCard;
