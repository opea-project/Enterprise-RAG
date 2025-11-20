// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { RootState } from "@/store";

export interface FileData {
  name: string;
  size: number;
  type: string;
  base64: string;
}

interface UploadFileTabState {
  fileData: FileData | null;
  summary: string;
  streamingText: string;
  isLoading: boolean;
  errorMessage: string;
}

const initialState: UploadFileTabState = {
  fileData: null,
  summary: "",
  streamingText: "",
  isLoading: false,
  errorMessage: "",
};

const uploadFileTabSlice = createSlice({
  name: "uploadFileTab",
  initialState,
  reducers: {
    setFileData: (state, action: PayloadAction<FileData | null>) => {
      state.fileData = action.payload;
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
    clearUploadFileTab: (state) => {
      state.fileData = null;
      state.summary = "";
      state.streamingText = "";
      state.errorMessage = "";
    },
    resetUploadFileTabSlice: () => initialState,
  },
});

export const {
  setFileData,
  setSummary,
  setStreamingText,
  setIsLoading,
  setErrorMessage,
  clearUploadFileTab,
  resetUploadFileTabSlice,
} = uploadFileTabSlice.actions;

export const selectUploadFileTabState = (state: RootState) =>
  state.uploadFileTab;

export default uploadFileTabSlice.reducer;
