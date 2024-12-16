// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { v4 as uuidv4 } from "uuid";

import { PromptRequestParams } from "@/api/models/chatQnA";
import ChatQnAService from "@/services/chatQnAService";
import { RootState } from "@/store/index";
import {
  handleBufferedResponse,
  handleError,
  handleStreamedResponse,
} from "@/utils/chat/conversationFeed";

interface ChatMessage {
  text: string;
  id: string;
  isUserMessage: boolean;
  isStreaming?: boolean;
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

export const postPrompt = createAsyncThunk(
  "conversationFeed/postPrompt",
  async (prompt: string, { dispatch, getState }) => {
    try {
      const rootState = getState() as RootState;
      const { hasInputGuard, hasOutputGuard } = rootState.chatQnAGraph;
      const promptRequestParams: PromptRequestParams =
        await ChatQnAService.getPromptRequestParams(
          hasInputGuard,
          hasOutputGuard,
        );

      const newAbortController = new AbortController();
      dispatch(setAbortController(newAbortController));
      const abortSignal = newAbortController.signal;

      const { streaming: isLLMStreaming } = promptRequestParams;
      const isStreamingEnabled = isLLMStreaming || hasOutputGuard;
      const handleResponse = isStreamingEnabled
        ? handleStreamedResponse
        : handleBufferedResponse;

      await handleResponse(prompt, promptRequestParams, abortSignal, dispatch);
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
    updateBotMessageText: (state, action: PayloadAction<string>) => {
      const previousMessages: ChatMessage[] = [...state.messages];
      const chunk = action.payload;
      state.messages = previousMessages.map((message) =>
        message.id === state.currentChatBotMessageId
          ? {
              ...message,
              text: message.text + chunk,
            }
          : message,
      );
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
