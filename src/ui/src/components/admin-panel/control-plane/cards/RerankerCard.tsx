// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/components/admin-panel/control-plane/cards";
import SelectedServiceCard from "@/components/admin-panel/control-plane/SelectedServiceCard/SelectedServiceCard";
import ServiceArgumentNumberInput from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  RerankerArgs,
  rerankerFormConfig,
} from "@/config/control-plane/reranker";
import useServiceCard from "@/utils/hooks/useServiceCard";

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
