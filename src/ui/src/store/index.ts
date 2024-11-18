// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { configureStore } from "@reduxjs/toolkit";

import chatQnAGraphReducer from "@/store/chatQnAGraph.slice";
import conversationFeedReducer from "@/store/conversationFeed.slice";

export const store = configureStore({
  reducer: {
    conversationFeed: conversationFeedReducer,
    chatQnAGraph: chatQnAGraphReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export type AppStore = typeof store;
