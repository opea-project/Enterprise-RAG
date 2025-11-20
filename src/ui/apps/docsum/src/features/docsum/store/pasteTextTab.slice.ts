// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { RootState } from "@/store";

interface PasteTextTabState {
  text: string;
  summary: string;
  streamingText: string;
  isLoading: boolean;
  errorMessage: string;
  isInvalid: boolean;
}

const initialState: PasteTextTabState = {
  text: "",
  summary: "",
  streamingText: "",
  isLoading: false,
  errorMessage: "",
  isInvalid: false,
};

const pasteTextTabSlice = createSlice({
  name: "pasteTextTab",
  initialState,
  reducers: {
    setText: (state, action: PayloadAction<string>) => {
      state.text = action.payload;
    },
    setSummary: (state, action: PayloadAction<string>) => {
      state.summary = action.payload;
    },
    setStreamingText: (state, action: PayloadAction<string>) => {
      state.streamingText = action.payload;
    },
    setIsLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setErrorMessage: (state, action: PayloadAction<string>) => {
      state.errorMessage = action.payload;
    },
    setIsInvalid: (state, action: PayloadAction<boolean>) => {
      state.isInvalid = action.payload;
    },
    clearPasteTextTab: (state) => {
      state.text = "";
      state.summary = "";
      state.streamingText = "";
    },
    resetPasteTextTabSlice: () => initialState,
  },
});

export const {
  setText,
  setSummary,
  setStreamingText,
  setIsLoading,
  setErrorMessage,
  setIsInvalid,
  clearPasteTextTab,
  resetPasteTextTabSlice,
} = pasteTextTabSlice.actions;

export const selectPasteTextTabState = (state: RootState) => state.pasteTextTab;

export default pasteTextTabSlice.reducer;
