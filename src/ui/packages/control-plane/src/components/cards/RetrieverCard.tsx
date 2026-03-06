// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { RetrieverDebugDialog } from "@/components/cards/debug/RetrieverDebugDialog/RetrieverDebugDialog";
import { SelectedServiceCard } from "@/components/SelectedServiceCard/SelectedServiceCard";
import { ServiceArgumentNumberInput } from "@/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentSelectInput } from "@/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import { ServiceArgumentsTitle } from "@/components/ServiceArgumentsTitle/ServiceArgumentsTitle";
import { RerankerArgs } from "@/configs/services/reranker";
import {
  RetrieverArgs,
  retrieverFormConfig,
  searchTypesArgsMap,
} from "@/configs/services/retriever";
import { useServiceCard } from "@/hooks/useServiceCard";
import { PostRetrieverQueryRequest } from "@/types/api/requests";
import { ControlPlaneCardProps } from "@/types/cards";
import {
  createFilterInvalidRetrieverArguments,
  createFilterRetrieverFormData,
} from "@/utils/card";

export interface RetrieverCardProps extends ControlPlaneCardProps {
  isDebugEnabled?: boolean;
  rerankerArgs?: RerankerArgs;
  onPostRetrieverQuery?: (
    request: PostRetrieverQueryRequest,
  ) => Promise<{ data?: unknown; error?: unknown }>;
  onGetErrorMessage?: (error: unknown, defaultMessage: string) => string;
}

export const RetrieverCard = ({
  data: { id, status, displayName, retrieverArgs },
  changeArguments,
  isDebugEnabled,
  rerankerArgs,
  onPostRetrieverQuery,
  onGetErrorMessage,
}: RetrieverCardProps) => {
  const config = retrieverFormConfig;

  const {
    argumentsForm,
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps,
  } = useServiceCard<RetrieverArgs>(id, retrieverArgs, {
    changeArguments,
    filterFns: {
      filterFormData: createFilterRetrieverFormData(searchTypesArgsMap),
      filterInvalidArguments:
        createFilterInvalidRetrieverArguments(searchTypesArgsMap),
    },
  });

  const DebugDialog =
    isDebugEnabled && onPostRetrieverQuery && onGetErrorMessage ? (
      <RetrieverDebugDialog
        retrieverArgs={retrieverArgs}
        rerankerArgs={rerankerArgs}
        onPostRetrieverQuery={onPostRetrieverQuery}
        onGetErrorMessage={onGetErrorMessage}
      />
    ) : undefined;

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
      <ServiceArgumentsTitle>Service Arguments</ServiceArgumentsTitle>
      <ServiceArgumentSelectInput
        {...config.search_type}
        value={argumentsForm.search_type}
        onArgumentValueChange={onArgumentValueChange}
      />
      {visibleArgumentInputs.includes(config.k.name) && (
        <ServiceArgumentNumberInput
          {...config.k}
          value={argumentsForm.k}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(config.distance_threshold.name) && (
        <ServiceArgumentNumberInput
          {...config.distance_threshold}
          value={argumentsForm.distance_threshold}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(config.fetch_k.name) && (
        <ServiceArgumentNumberInput
          {...config.fetch_k}
          value={argumentsForm.fetch_k}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(config.lambda_mult.name) && (
        <ServiceArgumentNumberInput
          {...config.lambda_mult}
          value={argumentsForm.lambda_mult}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
      {visibleArgumentInputs.includes(config.score_threshold.name) && (
        <ServiceArgumentNumberInput
          {...config.score_threshold}
          value={argumentsForm.score_threshold}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      )}
    </SelectedServiceCard>
  );
};
