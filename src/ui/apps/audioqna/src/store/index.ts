// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  colorSchemeReducer,
  notificationsReducer,
} from "@intel-enterprise-rag-ui/components";
import { configureStore } from "@reduxjs/toolkit";

import { appApi } from "@/api";
// import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import { edpApi } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { dataIngestionApiMiddleware } from "@/features/admin-panel/data-ingestion/api/middleware";
import { s3Api } from "@/features/admin-panel/data-ingestion/api/s3Api";
import dataIngestionSettingsReducer from "@/features/admin-panel/data-ingestion/store/dataIngestionSettings.slice";
import { chatHistoryApi } from "@/features/chat/api/chatHistory";
import { chatQnAApi } from "@/features/chat/api/chatQnA";
import chatHistoryReducer from "@/features/chat/store/chatHistory.slice";
import chatSideMenusReducer from "@/features/chat/store/chatSideMenus.slice";
import viewNavigationReducer from "@/store/viewNavigation.slice";

export const store = configureStore({
  reducer: {
    chatSideMenus: chatSideMenusReducer,
    chatHistory: chatHistoryReducer,
    colorScheme: colorSchemeReducer,
    notifications: notificationsReducer,
    dataIngestionSettings: dataIngestionSettingsReducer,
    viewNavigation: viewNavigationReducer,
    [appApi.reducerPath]: appApi.reducer,
    [chatQnAApi.reducerPath]: chatQnAApi.reducer,
    [chatHistoryApi.reducerPath]: chatHistoryApi.reducer,
    // [controlPlaneApi.reducerPath]: controlPlaneApi.reducer,
    [edpApi.reducerPath]: edpApi.reducer,
    [s3Api.reducerPath]: s3Api.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(
      appApi.middleware,
      chatQnAApi.middleware,
      chatHistoryApi.middleware,
      // controlPlaneApi.middleware,
      edpApi.middleware,
      s3Api.middleware,
      dataIngestionApiMiddleware,
    ),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export type AppStore = typeof store;
