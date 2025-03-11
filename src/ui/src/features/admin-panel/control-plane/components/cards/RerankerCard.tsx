// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";
import ServiceArgumentNumberInput from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  RerankerArgs,
  rerankerFormConfig,
} from "@/features/admin-panel/control-plane/config/reranker";
import useServiceCard from "@/features/admin-panel/control-plane/hooks/useServiceCard";

const RerankerCard = ({
  data: { id, status, displayName, rerankerArgs },
}: ControlPlaneCardProps) => {
  const {
    previousArgumentsValues,
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps,
  } = useServiceCard<RerankerArgs>(id, rerankerArgs);

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      footerProps={footerProps}
    >
      <p className="mb-1 mt-3 text-sm font-medium">Service Arguments</p>
      <ServiceArgumentNumberInput
        {...rerankerFormConfig.top_n}
        initialValue={previousArgumentsValues.top_n}
        onArgumentValueChange={onArgumentValueChange}
        onArgumentValidityChange={onArgumentValidityChange}
      />
    </SelectedServiceCard>
  );
};

export default RerankerCard;
