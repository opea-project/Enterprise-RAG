// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Middleware } from "@reduxjs/toolkit";

import { edpApi } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { s3Api } from "@/features/admin-panel/data-ingestion/api/s3Api";

export const dataIngestionApiMiddleware: Middleware =
  (middlewareApi) => (next) => (action) => {
    const result = next(action);

    if (s3Api.endpoints.deleteFile.matchFulfilled(action)) {
      middlewareApi.dispatch(edpApi.util.invalidateTags(["Files"]));
    }

    return result;
  };
