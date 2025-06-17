// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { RootState } from "@/store";
import { ConversationTurn } from "@/types";

interface ConversationState {
  userInput: string;
  conversationTurns: ConversationTurn[];
  currentConversationTurnId: string | null;
  isChatResponsePending: boolean;
  hasActiveRequest: boolean;
}

const initialState: ConversationState = {
  userInput: "",
  conversationTurns: [],
  currentConversationTurnId: null,
  isChatResponsePending: false,
  hasActiveRequest: false,
};

export const conversationFeedSlice = createSlice({
  name: "conversationFeed",
  initialState,
  reducers: {
    setUserInput: (state, action: PayloadAction<string>) => {
      state.userInput = action.payload;
    },
    addNewConversationTurn: (
      state,
      action: PayloadAction<Pick<ConversationTurn, "id" | "question">>,
    ) => {
      const { id, question } = action.payload;
      const newConversationTurn = {
        id,
        question,
        answer: "",
        error: null,
        isPending: true,
      };

      state.conversationTurns = [
        ...state.conversationTurns,
        newConversationTurn,
      ];
      state.currentConversationTurnId = id;
    },
    updateAnswer: (
      state,
      action: PayloadAction<ConversationTurn["answer"]>,
    ) => {
      const answer = action.payload;
      state.conversationTurns = state.conversationTurns.map((turn) =>
        turn.id === state.currentConversationTurnId
          ? {
              ...turn,
              answer: turn.answer ? `${turn.answer}${answer}` : answer,
            }
          : turn,
      );
    },
    updateError: (state, action: PayloadAction<ConversationTurn["error"]>) => {
      const error = action.payload;
      state.conversationTurns = state.conversationTurns.map((turn) =>
        turn.id === state.currentConversationTurnId
          ? { ...turn, error, isPending: false }
          : turn,
      );
    },
    updateIsPending: (
      state,
      action: PayloadAction<ConversationTurn["isPending"]>,
    ) => {
      const isPending = action.payload;
      state.conversationTurns = state.conversationTurns.map((turn) =>
        turn.id === state.currentConversationTurnId
          ? { ...turn, isPending }
          : turn,
      );
    },
    setIsChatResponsePending: (state, action: PayloadAction<boolean>) => {
      state.isChatResponsePending = action.payload;
      state.hasActiveRequest = action.payload;
    },
    resetConversationFeedSlice: () => initialState,
  },
});

export const {
  setUserInput,
  addNewConversationTurn,
  updateAnswer,
  updateError,
  updateIsPending,
  setIsChatResponsePending,
  resetConversationFeedSlice,
} = conversationFeedSlice.actions;

export const selectUserInput = (state: RootState) =>
  state.conversationFeed.userInput;
export const selectConversationTurns = (state: RootState) =>
  state.conversationFeed.conversationTurns;
export const selectIsChatResponsePending = (state: RootState) =>
  state.conversationFeed.isChatResponsePending;
export default conversationFeedSlice.reducer;
