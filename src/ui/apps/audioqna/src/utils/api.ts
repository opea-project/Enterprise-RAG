// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { addNotification } from "@intel-enterprise-rag-ui/components";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query/react";

import { NamespaceStatus } from "@/features/admin-panel/control-plane/types/api/namespaceStatus";
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

export const mergeNamespaceStatuses = (
  primaryStatus: NamespaceStatus,
  secondaryStatus: NamespaceStatus,
): NamespaceStatus => {
  // Handle audio status format (only has status.annotations)
  const primaryHasSpec = primaryStatus.spec?.nodes?.root?.steps;
  const secondaryHasSpec = secondaryStatus.spec?.nodes?.root?.steps;

  return {
    ...primaryStatus,
    spec:
      primaryHasSpec && secondaryHasSpec
        ? {
            ...primaryStatus.spec,
            nodes: {
              ...primaryStatus.spec.nodes,
              root: {
                ...primaryStatus.spec.nodes.root,
                steps: [
                  ...primaryStatus.spec.nodes.root.steps,
                  ...secondaryStatus.spec.nodes.root.steps,
                ],
              },
            },
          }
        : primaryStatus.spec || secondaryStatus.spec,
    status: {
      ...primaryStatus.status,
      ...secondaryStatus.status,
      annotations: {
        ...primaryStatus.status?.annotations,
        ...secondaryStatus.status?.annotations,
      },
    },
  };
};
