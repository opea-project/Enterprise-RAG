// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { RootState } from "@/store";

export type ProcessingTimeFormat = "standard" | "compact";

const localStorageKeys = {
  processingTimeFormat: "processingTimeFormat",
  isAutorefreshEnabled: "isAutorefreshEnabled",
} as const;

const defaultFormat = "standard";
const defaultIsAutorefreshEnabled = true;

const getProcessingTimeFormat = (): ProcessingTimeFormat => {
  const storedFormat = localStorage.getItem(
    localStorageKeys.processingTimeFormat,
  );
  if (storedFormat === "standard" || storedFormat === "compact") {
    return storedFormat as ProcessingTimeFormat;
  }
  return defaultFormat;
};

const getIsAutorefreshEnabled = () => {
  const isAutorefreshEnabled = localStorage.getItem(
    localStorageKeys.isAutorefreshEnabled,
  );
  if (isAutorefreshEnabled === null) {
    return defaultIsAutorefreshEnabled;
  }
  return isAutorefreshEnabled === "true" ? true : false;
};

interface DataIngestionSettingsState {
  processingTimeFormat: ProcessingTimeFormat;
  isAutorefreshEnabled: boolean;
}

const initialState: DataIngestionSettingsState = {
  processingTimeFormat: getProcessingTimeFormat(),
  isAutorefreshEnabled: getIsAutorefreshEnabled(),
};

const dataIngestionSettingsSlice = createSlice({
  name: "dataIngestionSettings",
  initialState,
  reducers: {
    setProcessingTimeFormat: (
      state,
      action: PayloadAction<ProcessingTimeFormat>,
    ) => {
      state.processingTimeFormat = action.payload;
      localStorage.setItem(
        localStorageKeys.processingTimeFormat,
        action.payload,
      );
    },
    setIsAutorefreshEnabled: (state, action: PayloadAction<boolean>) => {
      state.isAutorefreshEnabled = action.payload;
      localStorage.setItem(
        localStorageKeys.isAutorefreshEnabled,
        action.payload.toString(),
      );
    },
  },
});

export const { setProcessingTimeFormat, setIsAutorefreshEnabled } =
  dataIngestionSettingsSlice.actions;

export const selectProcessingTimeFormat = (state: RootState) =>
  state.dataIngestionSettings.processingTimeFormat;
export const selectIsAutorefreshEnabled = (state: RootState) =>
  state.dataIngestionSettings.isAutorefreshEnabled;

export default dataIngestionSettingsSlice.reducer;
