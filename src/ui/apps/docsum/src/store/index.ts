// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  colorSchemeReducer,
  notificationsReducer,
} from "@intel-enterprise-rag-ui/components";
import { configureStore } from "@reduxjs/toolkit";

import { summarizationApi } from "@/api";
import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import docSumGraphReducer from "@/features/admin-panel/control-plane/store/docSumGraph.slice";
import historyReducer from "@/features/docsum/tabs/history/store/history.slice";

export const store = configureStore({
  reducer: {
    colorScheme: colorSchemeReducer,
    history: historyReducer,
    notifications: notificationsReducer,
    docSumGraph: docSumGraphReducer,
    [summarizationApi.reducerPath]: summarizationApi.reducer,
    [controlPlaneApi.reducerPath]: controlPlaneApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(
      summarizationApi.middleware,
      controlPlaneApi.middleware,
    ),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export type AppStore = typeof store;
