// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  chatHistoryReducer,
  chatSideMenuReducer,
} from "@intel-enterprise-rag-ui/chat";
import {
  colorSchemeReducer,
  notificationsReducer,
} from "@intel-enterprise-rag-ui/components";
import { configureStore } from "@reduxjs/toolkit";

import { appApi } from "@/api";
import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import audioQnAGraphReducer from "@/features/admin-panel/control-plane/store/audioQnAGraph.slice";
import { edpApi } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { dataIngestionApiMiddleware } from "@/features/admin-panel/data-ingestion/api/middleware";
import { s3Api } from "@/features/admin-panel/data-ingestion/api/s3Api";
import dataIngestionSettingsReducer from "@/features/admin-panel/data-ingestion/store/dataIngestionSettings.slice";
import { asrApi } from "@/features/chat/api/asr.api";
import { audioQnAApi } from "@/features/chat/api/audioQnA.api";
import { chatHistoryApi } from "@/features/chat/api/chatHistory.api";
import { ttsApi } from "@/features/chat/api/tts.api";
import viewNavigationReducer from "@/store/viewNavigation.slice";

export const store = configureStore({
  reducer: {
    chatSideMenu: chatSideMenuReducer,
    chatHistory: chatHistoryReducer,
    colorScheme: colorSchemeReducer,
    notifications: notificationsReducer,
    audioQnAGraph: audioQnAGraphReducer,
    dataIngestionSettings: dataIngestionSettingsReducer,
    viewNavigation: viewNavigationReducer,
    [appApi.reducerPath]: appApi.reducer,
    [asrApi.reducerPath]: asrApi.reducer,
    [audioQnAApi.reducerPath]: audioQnAApi.reducer,
    [chatHistoryApi.reducerPath]: chatHistoryApi.reducer,
    [controlPlaneApi.reducerPath]: controlPlaneApi.reducer,
    [edpApi.reducerPath]: edpApi.reducer,
    [s3Api.reducerPath]: s3Api.reducer,
    [ttsApi.reducerPath]: ttsApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(
      appApi.middleware,
      asrApi.middleware,
      audioQnAApi.middleware,
      chatHistoryApi.middleware,
      controlPlaneApi.middleware,
      edpApi.middleware,
      s3Api.middleware,
      ttsApi.middleware,
      dataIngestionApiMiddleware,
    ),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export type AppStore = typeof store;
