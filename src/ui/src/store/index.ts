// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { configureStore } from "@reduxjs/toolkit";

import colorSchemeReducer from "@/components/ui/ColorSchemeSwitch/colorScheme.slice";
import notificationsReducer from "@/components/ui/Notifications/notifications.slice";
import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import chatQnAGraphReducer from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { edpApi } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { dataIngestionApiMiddleware } from "@/features/admin-panel/data-ingestion/api/middleware";
import { s3Api } from "@/features/admin-panel/data-ingestion/api/s3Api";
import dataIngestionSettingsReducer from "@/features/admin-panel/data-ingestion/store/dataIngestionSettings.slice";
import { chatQnAApi } from "@/features/chat/api";
import chatSideMenusReducer from "@/features/chat/store/chatSideMenus.slice";
import conversationFeedReducer from "@/features/chat/store/conversationFeed.slice";

export const store = configureStore({
  reducer: {
    conversationFeed: conversationFeedReducer,
    chatSideMenus: chatSideMenusReducer,
    chatQnAGraph: chatQnAGraphReducer,
    colorScheme: colorSchemeReducer,
    notifications: notificationsReducer,
    dataIngestionSettings: dataIngestionSettingsReducer,
    [chatQnAApi.reducerPath]: chatQnAApi.reducer,
    [controlPlaneApi.reducerPath]: controlPlaneApi.reducer,
    [edpApi.reducerPath]: edpApi.reducer,
    [s3Api.reducerPath]: s3Api.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(
      chatQnAApi.middleware,
      controlPlaneApi.middleware,
      edpApi.middleware,
      s3Api.middleware,
      dataIngestionApiMiddleware,
    ),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export type AppStore = typeof store;
