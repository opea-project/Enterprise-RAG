// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { RootState } from "@/store/index";

interface ChatFeedMessage {
  text: string;
  id: string;
  isUserMessage: boolean;
}

export interface ConversationFeedState {
  messages: ChatFeedMessage[];
  isMessageStreamed: boolean;
}

const initialState: ConversationFeedState = {
  messages: [],
  isMessageStreamed: false,
};

interface MessageUpdate {
  messageId: string;
  chunk: string;
}

export const conversationFeedSlice = createSlice({
  name: "conversationFeed",
  initialState,
  reducers: {
    addMessage: (state, action: PayloadAction<ChatFeedMessage>) => {
      state.messages = [...state.messages, action.payload];
    },
    updateMessage: (state, action: PayloadAction<MessageUpdate>) => {
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
    setIsMessageStreamed: (state, action: PayloadAction<boolean>) => {
      state.isMessageStreamed = action.payload;
    },
  },
});

export const { addMessage, updateMessage, setIsMessageStreamed } =
  conversationFeedSlice.actions;
export const selectMessages = (state: RootState) =>
  state.conversationFeed.messages;
export const selectIsMessageStreamed = (state: RootState) =>
  state.conversationFeed.isMessageStreamed;
export default conversationFeedSlice.reducer;
