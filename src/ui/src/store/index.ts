// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { configureStore } from "@reduxjs/toolkit";

import chatQnAGraphReducer from "@/store/chatQnAGraph.slice";
import colorSchemeReducer from "@/store/colorScheme.slice";
import conversationFeedReducer from "@/store/conversationFeed.slice";
import dataIngestionReducer from "@/store/dataIngestion.slice";
import notificationsReducer from "@/store/notifications.slice";

export const store = configureStore({
  reducer: {
    chatQnAGraph: chatQnAGraphReducer,
    colorScheme: colorSchemeReducer,
    conversationFeed: conversationFeedReducer,
    dataIngestion: dataIngestionReducer,
    notifications: notificationsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export type AppStore = typeof store;
