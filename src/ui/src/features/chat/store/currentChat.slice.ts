// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { SourceDocumentType } from "@/features/chat/types";
import { RootState } from "@/store";
import { ChatTurn } from "@/types";

interface ConversationState {
  userInput: string;
  chatId?: string;
  chatTurns: ChatTurn[];
  chatSources: SourceDocumentType[][];
  currentChatTurnId: string | null;
  isChatResponsePending: boolean;
  hasActiveRequest: boolean;
}

const initialState: ConversationState = {
  userInput: "",
  chatId: undefined,
  chatTurns: [],
  chatSources: [],
  currentChatTurnId: null,
  isChatResponsePending: false,
  hasActiveRequest: false,
};

export const currentChatSlice = createSlice({
  name: "currentChat",
  initialState,
  reducers: {
    setUserInput: (state, action: PayloadAction<string>) => {
      state.userInput = action.payload;
    },
    setCurrentChatId: (state, action: PayloadAction<string | undefined>) => {
      state.chatId = action.payload;
    },
    setCurrentChatTurns: (state, action: PayloadAction<ChatTurn[]>) => {
      state.chatTurns = action.payload;
      if (action.payload.length > 0) {
        state.currentChatTurnId = action.payload[0].id;
      } else {
        state.currentChatTurnId = null;
      }
    },
    setCurrentChatSources: (
      state,
      action: PayloadAction<SourceDocumentType[][]>,
    ) => {
      state.chatSources = action.payload;
    },
    addNewChatTurn: (
      state,
      action: PayloadAction<Pick<ChatTurn, "id" | "question">>,
    ) => {
      const { id, question } = action.payload;
      const newChatTurn: ChatTurn = {
        id,
        question,
        answer: "",
        error: null,
        isPending: true,
        sources: [],
      };

      state.chatTurns = [...state.chatTurns, newChatTurn];
      state.currentChatTurnId = id;
    },
    updateAnswer: (state, action: PayloadAction<ChatTurn["answer"]>) => {
      const answerChunk = action.payload;
      state.chatTurns = state.chatTurns.map((turn) =>
        turn.id === state.currentChatTurnId
          ? {
              ...turn,
              answer: turn.answer
                ? `${turn.answer}${answerChunk}`
                : answerChunk,
            }
          : turn,
      );
    },
    updateSources: (state, action: PayloadAction<SourceDocumentType[]>) => {
      const sources = Array.from(
        new Map(
          action.payload
            .filter((src) => src.citation_id)
            .map((src) => [src.citation_id, src]),
        ).values(),
      );
      state.chatSources = [...state.chatSources, sources];
    },
    updateError: (state, action: PayloadAction<ChatTurn["error"]>) => {
      const error = action.payload;
      state.chatTurns = state.chatTurns.map((turn) =>
        turn.id === state.currentChatTurnId
          ? { ...turn, error, isPending: false }
          : turn,
      );
    },
    updateIsPending: (state, action: PayloadAction<ChatTurn["isPending"]>) => {
      const isPending = action.payload;
      state.chatTurns = state.chatTurns.map((turn) =>
        turn.id === state.currentChatTurnId ? { ...turn, isPending } : turn,
      );
    },
    setIsChatResponsePending: (state, action: PayloadAction<boolean>) => {
      state.isChatResponsePending = action.payload;
      state.hasActiveRequest = action.payload;
    },
    resetCurrentChatSlice: () => initialState,
  },
});

export const {
  setUserInput,
  setCurrentChatId,
  setCurrentChatTurns,
  setCurrentChatSources,
  addNewChatTurn,
  updateAnswer,
  updateSources,
  updateError,
  updateIsPending,
  setIsChatResponsePending,
  resetCurrentChatSlice,
} = currentChatSlice.actions;

export const selectUserInput = (state: RootState) =>
  state.currentChat.userInput;
export const selectCurrentChatId = (state: RootState) =>
  state.currentChat.chatId;
export const selectCurrentChatTurns = (state: RootState) =>
  state.currentChat.chatTurns;
export const selectCurrentChatSources = (state: RootState) =>
  state.currentChat.chatSources;
export const selectIsChatResponsePending = (state: RootState) =>
  state.currentChat.isChatResponsePending;
export default currentChatSlice.reducer;
