// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FetchBaseQueryError } from "@reduxjs/toolkit/query/react";

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

const onRefreshTokenFailed = () => {
  keycloakService.redirectToLogout();
  resetStore();
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

export { getErrorMessage, onRefreshTokenFailed, transformErrorMessage };
