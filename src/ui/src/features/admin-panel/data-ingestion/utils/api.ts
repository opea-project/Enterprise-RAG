// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FetchBaseQueryError } from "@reduxjs/toolkit/query";

import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { ExtractTextQueryParamsFormData } from "@/features/admin-panel/data-ingestion/types";
import { PostFileToExtractTextQueryParams } from "@/features/admin-panel/data-ingestion/types/api";
import { AppDispatch } from "@/store";
import { getErrorMessage } from "@/utils/api";

const createPostFileToExtractTextQueryParams = (
  queryParamsObj: ExtractTextQueryParamsFormData,
): PostFileToExtractTextQueryParams => {
  const queryParamsEntries = Object.entries(queryParamsObj)
    .map(([key, value]) =>
      key === "table_strategy"
        ? [key, value === true ? "fast" : undefined]
        : [key, value],
    )
    .filter(([, value]) => value !== undefined);

  return Object.fromEntries(queryParamsEntries);
};

const handleOnQueryStarted = async <T>(
  queryFulfilled: Promise<T>,
  dispatch: AppDispatch,
  fallbackMessage: string,
) => {
  try {
    await queryFulfilled;
  } catch (error) {
    const errorMessage = getErrorMessage(
      (error as { error: FetchBaseQueryError }).error,
      fallbackMessage,
    );
    dispatch(addNotification({ severity: "error", text: errorMessage }));
  }
};

export { createPostFileToExtractTextQueryParams, handleOnQueryStarted };
