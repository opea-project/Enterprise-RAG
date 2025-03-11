// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { v4 as uuidv4 } from "uuid";

import { postPrompt } from "@/features/chat/api/postPrompt";
import { UpdatedChatMessage } from "@/features/chat/types";
import { handleError } from "@/features/chat/utils/conversationFeed";
import { RootState } from "@/store/index";

interface ChatMessage {
  text: string;
  id: string;
  isUserMessage: boolean;
  isStreaming?: boolean;
  isError?: boolean;
}

interface ConversationFeedState {
  messages: ChatMessage[];
  isStreaming: boolean;
  currentChatBotMessageId: string | null;
  abortController: AbortController | null;
}

const initialState: ConversationFeedState = {
  messages: [],
  isStreaming: false,
  currentChatBotMessageId: null,
  abortController: null,
};

export const sendPrompt = createAsyncThunk(
  "conversationFeed/sendPrompt",
  async (prompt: string, { dispatch }) => {
    try {
      const newAbortController = new AbortController();
      dispatch(setAbortController(newAbortController));
      const abortSignal = newAbortController.signal;
      await postPrompt(prompt, abortSignal, dispatch);
    } catch (error) {
      const errorMessage = handleError(error);
      dispatch(updateBotMessageText(errorMessage));
    } finally {
      dispatch(updateMessageIsStreamed(false));
      dispatch(setAbortController(null));
    }
  },
);

export const conversationFeedSlice = createSlice({
  name: "conversationFeed",
  initialState,
  reducers: {
    addNewUserMessage: (state, action: PayloadAction<string>) => {
      const prompt = action.payload;
      const newUserMessage = {
        id: uuidv4(),
        text: prompt,
        isUserMessage: true,
      };
      state.messages = [...state.messages, newUserMessage];
    },
    addNewBotMessage: (state) => {
      const id = uuidv4();
      const newBotMessage = {
        id,
        text: "",
        isUserMessage: false,
        isStreaming: true,
      };
      state.messages = [...state.messages, newBotMessage];
      state.currentChatBotMessageId = id;
      state.isStreaming = true;
    },
    setAbortController: (
      state,
      action: PayloadAction<AbortController | null>,
    ) => {
      state.abortController = action.payload;
    },
    updateBotMessageText: (
      state,
      action: PayloadAction<string | UpdatedChatMessage>,
    ) => {
      const previousMessages: ChatMessage[] = [...state.messages];
      if (typeof action.payload === "string") {
        const chunk = action.payload;
        state.messages = previousMessages.map((message) =>
          message.id === state.currentChatBotMessageId
            ? {
                ...message,
                text: `${message.text}${chunk}`,
              }
            : message,
        );
      } else {
        const { text, isError } = action.payload;
        state.messages = previousMessages.map((message) =>
          message.id === state.currentChatBotMessageId
            ? {
                ...message,
                text: `${message.text}${text}`,
                isError,
              }
            : message,
        );
      }
    },
    updateMessageIsStreamed: (state, action: PayloadAction<boolean>) => {
      const previousMessages: ChatMessage[] = [...state.messages];
      const isStreaming = action.payload;
      state.messages = previousMessages.map((message) =>
        message.id === state.currentChatBotMessageId
          ? {
              ...message,
              isStreaming,
            }
          : message,
      );
      if (!isStreaming) {
        state.currentChatBotMessageId = null;
      }
      state.isStreaming = isStreaming;
    },
  },
});

export const {
  addNewUserMessage,
  addNewBotMessage,
  setAbortController,
  updateBotMessageText,
  updateMessageIsStreamed,
} = conversationFeedSlice.actions;
export const selectMessages = (state: RootState) =>
  state.conversationFeed.messages;
export const selectIsStreaming = (state: RootState) =>
  state.conversationFeed.isStreaming;
export const selectAbortController = (state: RootState) =>
  state.conversationFeed.abortController;
export default conversationFeedSlice.reducer;
