// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { RootState } from "@/store/index";

interface ChatFeedMessage {
  text: string;
  id: string;
  isUserMessage: boolean;
  isStreaming?: boolean;
}

export interface ConversationFeedState {
  messages: ChatFeedMessage[];
  isStreaming: boolean;
}

const initialState: ConversationFeedState = {
  messages: [],
  isStreaming: false,
};

interface MessageTextUpdate {
  messageId: string;
  chunk: string;
}
interface MessageIsStreamedUpdate {
  messageId: string;
  isStreaming: boolean;
}

export const conversationFeedSlice = createSlice({
  name: "conversationFeed",
  initialState,
  reducers: {
    addMessage: (state, action: PayloadAction<ChatFeedMessage>) => {
      state.messages = [...state.messages, action.payload];
    },
    updateMessageText: (state, action: PayloadAction<MessageTextUpdate>) => {
      const previousMessages: ChatFeedMessage[] = [...state.messages];
      const { messageId, chunk } = action.payload;
      state.messages = previousMessages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              text: message.text + chunk,
            }
          : message,
      );
    },
    updateMessageIsStreamed: (
      state,
      action: PayloadAction<MessageIsStreamedUpdate>,
    ) => {
      const previousMessages: ChatFeedMessage[] = [...state.messages];
      const { messageId, isStreaming } = action.payload;
      state.messages = previousMessages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              isStreaming,
            }
          : message,
      );
    },
    setIsStreaming: (state, action: PayloadAction<boolean>) => {
      state.isStreaming = action.payload;
    },
  },
});

export const {
  addMessage,
  updateMessageText,
  updateMessageIsStreamed,
  setIsStreaming,
} = conversationFeedSlice.actions;
export const selectMessages = (state: RootState) =>
  state.conversationFeed.messages;
export const selectIsStreaming = (state: RootState) =>
  state.conversationFeed.isStreaming;
export default conversationFeedSlice.reducer;
