// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FetchBaseQueryError } from "@reduxjs/toolkit/query";

import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { AppDispatch } from "@/store";
import { getErrorMessage } from "@/utils/api";

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

export { handleOnQueryStarted };
