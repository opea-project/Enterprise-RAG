// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/components/admin-panel/control-plane/cards";
import SelectedServiceCard from "@/components/admin-panel/control-plane/SelectedServiceCard/SelectedServiceCard";
import ServiceArgumentNumberInput from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import ServiceArgumentSelectInput from "@/components/admin-panel/control-plane/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import {
  RetrieverArgs,
  retrieverFormConfig,
  searchTypesArgsMap,
} from "@/config/control-plane/retriever";
import useServiceCard, {
  FilterFormDataFunction,
  FilterInvalidArgumentsFunction,
} from "@/utils/hooks/useServiceCard";

const filterFormData: FilterFormDataFunction<RetrieverArgs> = (data) => {
  if (data?.search_type) {
    const visibleInputs = searchTypesArgsMap[data.search_type];
    const copyData: Partial<RetrieverArgs> = { search_type: data.search_type };
    for (const argumentName in data) {
      if (visibleInputs.includes(argumentName)) {
        copyData[argumentName] = data[argumentName];
      }
    }
    return copyData;
  } else {
    return data;
  }
};

const filterInvalidArguments: FilterInvalidArgumentsFunction<RetrieverArgs> = (
  invalidArguments,
  data,
) => {
  if (data?.search_type) {
    const visibleInputs = searchTypesArgsMap[data.search_type];
    return invalidArguments.filter((arg) => visibleInputs.includes(arg));
  } else {
    return invalidArguments;
  }
};

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
    filterFormData,
    filterInvalidArguments,
  });

  const visibleArgumentInputs = argumentsForm?.search_type
    ? searchTypesArgsMap[argumentsForm.search_type]
    : [];

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      serviceDetails={details}
      footerProps={footerProps}
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
