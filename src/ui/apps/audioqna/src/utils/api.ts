// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { addNotification } from "@intel-enterprise-rag-ui/components";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query/react";

import { AppDispatch } from "@/store";
import { resetStore } from "@/store/utils";
import { keycloakService } from "@/utils/auth";

const getErrorMessage = (error: unknown, fallbackMessage: string): string => {
  if (typeof error === "object" && error !== null) {
    const fetchError = error as FetchBaseQueryError;

    if (typeof fetchError.status === "number") {
      if (typeof fetchError.data === "object" && fetchError.data !== null) {
        if (
          "message" in fetchError.data &&
          typeof fetchError.data.message === "string"
        ) {
          return fetchError.data.message;
        } else if (
          "detail" in fetchError.data &&
          typeof fetchError.data.detail === "string"
        ) {
          return fetchError.data.detail;
        }
      }

      return JSON.stringify(fetchError.data);
    } else if (
      "originalStatus" in fetchError &&
      typeof fetchError.originalStatus === "number"
    ) {
      if (fetchError.originalStatus === 429) {
        return "Too many requests. Please try again later.";
      }

      return fetchError.error;
    } else if ("error" in fetchError) {
      return fetchError.error;
    }
  }

  return fallbackMessage;
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

const onRefreshTokenFailed = () => {
  resetStore();
  keycloakService.redirectToLogout();
};

const transformErrorMessage = (
  error: FetchBaseQueryError,
  fallbackMessage: string,
): FetchBaseQueryError => {
  if (error.status === "FETCH_ERROR") {
    return { ...error, error: fallbackMessage };
  } else {
    return error;
  }
};

export {
  getErrorMessage,
  handleOnQueryStarted,
  onRefreshTokenFailed,
  transformErrorMessage,
};
