// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  colorSchemeReducer,
  notificationsReducer,
} from "@intel-enterprise-rag-ui/components";
import { configureStore } from "@reduxjs/toolkit";

import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import docSumGraphReducer from "@/features/admin-panel/control-plane/store/docSumGraph.slice";
import { summarizationApi } from "@/features/docsum/api";
import historyReducer from "@/features/docsum/store/history.slice";
import pasteTextTabReducer from "@/features/docsum/store/pasteTextTab.slice";
import uploadFileTabReducer from "@/features/docsum/store/uploadFileTab.slice";

export const store = configureStore({
  reducer: {
    colorScheme: colorSchemeReducer,
    history: historyReducer,
    notifications: notificationsReducer,
    docSumGraph: docSumGraphReducer,
    pasteTextTab: pasteTextTabReducer,
    uploadFileTab: uploadFileTabReducer,
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
