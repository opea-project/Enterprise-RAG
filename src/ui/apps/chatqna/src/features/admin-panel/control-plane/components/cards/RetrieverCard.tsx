// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import RetrieverDebugDialog from "@/features/admin-panel/control-plane/components/cards/debug/RetrieverDebugDialog";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";
import ServiceArgumentNumberInput from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import ServiceArgumentSelectInput from "@/features/admin-panel/control-plane/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import {
  RetrieverArgs,
  retrieverFormConfig,
  searchTypesArgsMap,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/retriever";
import useServiceCard from "@/features/admin-panel/control-plane/hooks/useServiceCard";
import {
  filterInvalidRetrieverArguments,
  filterRetrieverFormData,
} from "@/features/admin-panel/control-plane/utils";
import useDebug from "@/hooks/useDebug";

const RetrieverCard = ({
  data: { id, status, displayName, retrieverArgs },
}: ControlPlaneCardProps) => {
  const {
    argumentsForm,
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps,
  } = useServiceCard<RetrieverArgs>(id, retrieverArgs, {
    filterFormData: filterRetrieverFormData,
    filterInvalidArguments: filterInvalidRetrieverArguments,
  });

  const { isDebugEnabled } = useDebug();
  const DebugDialog = isDebugEnabled ? <RetrieverDebugDialog /> : undefined;

  const visibleArgumentInputs = argumentsForm?.search_type
    ? searchTypesArgsMap[argumentsForm.search_type]
    : [];

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      footerProps={footerProps}
      DebugDialog={DebugDialog}
    >
      <p className="mb-2 mt-3 text-sm font-medium">Service Arguments</p>
      <ServiceArgumentSelectInput
        {...retrieverFormConfig.search_type}
        value={argumentsForm.search_type}
        onArgumentValueChange={onArgumentValueChange}
      />
      {visibleArgumentInputs.includes(retrieverFormConfig.k.name) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.k}
          value={argumentsForm.k}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(
        retrieverFormConfig.distance_threshold.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.distance_threshold}
          value={argumentsForm.distance_threshold}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(retrieverFormConfig.fetch_k.name) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.fetch_k}
          value={argumentsForm.fetch_k}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(retrieverFormConfig.lambda_mult.name) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.lambda_mult}
          value={argumentsForm.lambda_mult}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(
        retrieverFormConfig.score_threshold.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.score_threshold}
          value={argumentsForm.score_threshold}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
    </SelectedServiceCard>
  );
};

export default RetrieverCard;
