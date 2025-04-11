// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  RetrieverArgs,
  searchTypesArgsMap,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/retriever";
import {
  FilterFormDataFunction,
  FilterInvalidArgumentsFunction,
} from "@/features/admin-panel/control-plane/hooks/useServiceCard";

export const filterRetrieverFormData: FilterFormDataFunction<RetrieverArgs> = (
  data,
) => {
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

export const filterInvalidRetrieverArguments: FilterInvalidArgumentsFunction<
  RetrieverArgs
> = (invalidArguments, data) => {
  if (data?.search_type) {
    const visibleInputs = searchTypesArgsMap[data.search_type];
    return invalidArguments.filter((arg) => visibleInputs.includes(arg));
  } else {
    return invalidArguments;
  }
};
