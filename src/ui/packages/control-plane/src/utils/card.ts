// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  FilterFormDataFunction,
  FilterInvalidArgumentsFunction,
} from "@/hooks/useServiceCard";

/**
 * Creates a filter function for retriever form data based on search type visibility map
 */
export const createFilterRetrieverFormData = <
  T extends { search_type?: string },
>(
  searchTypesArgsMap: Record<string, string[]>,
): FilterFormDataFunction<T> => {
  return (data) => {
    if (data?.search_type) {
      const visibleInputs = searchTypesArgsMap[data.search_type];
      const copyData: Partial<T> = {
        search_type: data.search_type,
      } as Partial<T>;
      for (const argumentName in data) {
        if (visibleInputs.includes(argumentName)) {
          copyData[argumentName as keyof T] = data[argumentName];
        }
      }
      return copyData;
    } else {
      return data;
    }
  };
};

/**
 * Creates a filter function for invalid retriever arguments based on search type visibility map
 */
export const createFilterInvalidRetrieverArguments = <
  T extends { search_type?: string },
>(
  searchTypesArgsMap: Record<string, string[]>,
): FilterInvalidArgumentsFunction<T> => {
  return (invalidArguments, data) => {
    if (data?.search_type) {
      const visibleInputs = searchTypesArgsMap[data.search_type];
      return invalidArguments.filter((arg) => visibleInputs.includes(arg));
    } else {
      return invalidArguments;
    }
  };
};
