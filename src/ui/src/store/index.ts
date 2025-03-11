// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { configureStore } from "@reduxjs/toolkit";

import colorSchemeReducer from "@/components/ui/ColorSchemeSwitch/colorScheme.slice";
import notificationsReducer from "@/components/ui/Notifications/notifications.slice";
import chatQnAGraphReducer from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import dataIngestionReducer from "@/features/admin-panel/data-ingestion/store/dataIngestion.slice";
import conversationFeedReducer from "@/features/chat/store/conversationFeed.slice";

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
