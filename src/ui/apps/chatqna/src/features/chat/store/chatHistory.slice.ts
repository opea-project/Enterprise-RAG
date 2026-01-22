// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit/react";

import { SourceDocumentType } from "@/features/chat/types";
import { parseSources } from "@/features/chat/utils";
import { RootState } from "@/store";
import { Chat, ChatTurn } from "@/types";

interface ChatHistoryState {
  chats: Chat[];
}

const initialState: ChatHistoryState = {
  chats: [],
};

export const chatHistorySlice = createSlice({
  name: "chatHistory",
  initialState,
  reducers: {
    setChatHistory: (state, action: PayloadAction<Chat[]>) => {
      state.chats = action.payload;
    },
    addChat: (state, action: PayloadAction<Chat>) => {
      state.chats.push(action.payload);
    },
    updateChat: (state, action: PayloadAction<Chat>) => {
      const index = state.chats.findIndex(
        (chat) => chat.id === action.payload.id,
      );
      if (index !== -1) {
        state.chats[index] = action.payload;
      }
    },
    deleteChat: (state, action: PayloadAction<string>) => {
      state.chats = state.chats.filter((chat) => chat.id !== action.payload);
    },
    setChatTitle: (
      state,
      action: PayloadAction<{ id: string; title: string }>,
    ) => {
      const chat = state.chats.find((chat) => chat.id === action.payload.id);
      if (chat) {
        chat.title = action.payload.title;
      }
    },
    setChatTurns: (
      state,
      action: PayloadAction<{ id: string; turns: ChatTurn[] }>,
    ) => {
      const chat = state.chats.find((chat) => chat.id === action.payload.id);
      if (chat) {
        chat.turns = action.payload.turns;
      }
    },
    setChatInputValue: (
      state,
      action: PayloadAction<{ id: string; inputValue: string }>,
    ) => {
      const chat = state.chats.find((chat) => chat.id === action.payload.id);
      if (chat) {
        chat.inputValue = action.payload.inputValue;
      }
    },
    addChatTurn: (
      state,
      action: PayloadAction<{
        chatId: string;
        turn: Pick<ChatTurn, "id" | "question">;
      }>,
    ) => {
      const chat = state.chats.find(
        (chat) => chat.id === action.payload.chatId,
      );
      if (chat) {
        const { id, question } = action.payload.turn;
        const newChatTurn: ChatTurn = {
          id,
          question,
          answer: "",
          error: null,
          isPending: true,
          sources: [],
        };
        chat.turns.push(newChatTurn);
      }
    },
    updateChatTurnAnswer: (
      state,
      action: PayloadAction<{
        chatId: string;
        turnId: string;
        answerChunk: string;
      }>,
    ) => {
      const chat = state.chats.find(
        (chat) => chat.id === action.payload.chatId,
      );
      if (chat) {
        const turn = chat.turns.find(
          (turn) => turn.id === action.payload.turnId,
        );
        if (turn) {
          turn.answer = turn.answer
            ? `${turn.answer}${action.payload.answerChunk}`
            : action.payload.answerChunk;
        }
      }
    },
    updateChatTurnSources: (
      state,
      action: PayloadAction<{
        chatId: string;
        turnId: string;
        sources: SourceDocumentType[];
      }>,
    ) => {
      const chat = state.chats.find(
        (chat) => chat.id === action.payload.chatId,
      );
      if (chat) {
        const turn = chat.turns.find(
          (turn) => turn.id === action.payload.turnId,
        );
        if (turn) {
          const parsedSources = parseSources(action.payload.sources);
          turn.sources = parsedSources.length > 0 ? parsedSources : [];
        }
      }
    },
    updateChatTurnError: (
      state,
      action: PayloadAction<{
        chatId: string;
        turnId: string;
        error: string | null;
      }>,
    ) => {
      const chat = state.chats.find(
        (chat) => chat.id === action.payload.chatId,
      );
      if (chat) {
        const turn = chat.turns.find(
          (turn) => turn.id === action.payload.turnId,
        );
        if (turn) {
          turn.error = action.payload.error;
          turn.isPending = false;
        }
      }
    },
    updateChatTurnIsPending: (
      state,
      action: PayloadAction<{
        chatId: string;
        turnId: string;
        isPending: boolean;
      }>,
    ) => {
      const chat = state.chats.find(
        (chat) => chat.id === action.payload.chatId,
      );
      if (chat) {
        const turn = chat.turns.find(
          (turn) => turn.id === action.payload.turnId,
        );
        if (turn) {
          turn.isPending = action.payload.isPending;
        }
      }
    },
    resetChatHistorySlice: () => initialState,
  },
});

export const {
  setChatHistory,
  addChat,
  updateChat,
  deleteChat,
  setChatTitle,
  setChatTurns,
  setChatInputValue,
  addChatTurn,
  updateChatTurnAnswer,
  updateChatTurnSources,
  updateChatTurnError,
  updateChatTurnIsPending,
  resetChatHistorySlice,
} = chatHistorySlice.actions;

export const selectChatHistory = (state: RootState) => state.chatHistory.chats;

export const selectChatById = (state: RootState, chatId: string | undefined) =>
  chatId
    ? state.chatHistory.chats.find((chat) => chat.id === chatId)
    : undefined;

export const selectChatTurns = (
  state: RootState,
  chatId: string | undefined,
) =>
  chatId
    ? state.chatHistory.chats.find((chat) => chat.id === chatId)?.turns || []
    : [];

export default chatHistorySlice.reducer;
