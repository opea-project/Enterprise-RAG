// Copyright (C) 2024-2025 Intel Corporation
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
} from "@/features/admin-panel/control-plane/config/retriever";
import useServiceCard from "@/features/admin-panel/control-plane/hooks/useServiceCard";
import {
  filterInvalidRetrieverArguments,
  filterRetrieverFormData,
} from "@/features/admin-panel/control-plane/utils";
import useDebug from "@/hooks/useDebug";

const RetrieverCard = ({
  data: { id, status, displayName, retrieverArgs, details },
}: ControlPlaneCardProps) => {
  const {
    argumentsForm,
    previousArgumentsValues,
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
      serviceDetails={details}
      footerProps={footerProps}
      DebugDialog={DebugDialog}
    >
      <p className="mb-1 mt-3 text-sm font-medium">Service Arguments</p>
      <ServiceArgumentSelectInput
        {...retrieverFormConfig.search_type}
        initialValue={previousArgumentsValues.search_type}
        onArgumentValueChange={onArgumentValueChange}
      />
      {visibleArgumentInputs.includes(retrieverFormConfig.k.name) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.k}
          initialValue={previousArgumentsValues.k}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(
        retrieverFormConfig.distance_threshold.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.distance_threshold}
          initialValue={previousArgumentsValues.distance_threshold}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(retrieverFormConfig.fetch_k.name) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.fetch_k}
          initialValue={previousArgumentsValues.fetch_k}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(retrieverFormConfig.lambda_mult.name) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.lambda_mult}
          initialValue={previousArgumentsValues.lambda_mult}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(
        retrieverFormConfig.score_threshold.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.score_threshold}
          initialValue={previousArgumentsValues.score_threshold}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
    </SelectedServiceCard>
  );
};

export default RetrieverCard;
