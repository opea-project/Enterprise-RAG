// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  createAsyncThunk,
  createSlice,
  PayloadAction,
  SerializedError,
} from "@reduxjs/toolkit";

import { Notification } from "@/components/shared/NotificationToast/NotificationToast";
import {
  FileDataItem,
  LinkDataItem,
} from "@/models/admin-panel/data-ingestion/dataIngestion";
import DataIngestionService from "@/services/dataIngestionService";
import { RootState } from "@/store/index";

interface DataIngestionState {
  files: {
    data: FileDataItem[];
    isLoading: boolean;
    error: SerializedError | null;
  };
  links: {
    data: LinkDataItem[];
    isLoading: boolean;
    error: SerializedError | null;
  };
  notification: Notification;
}

const initialState: DataIngestionState = {
  files: {
    data: [],
    isLoading: false,
    error: null,
  },
  links: {
    data: [],
    isLoading: false,
    error: null,
  },
  notification: {
    open: false,
    message: "",
    severity: "success",
  },
};

export const getFiles = createAsyncThunk(
  "dataIngestion/getFiles",
  async () => await DataIngestionService.getFiles(),
);

export const getLinks = createAsyncThunk(
  "dataIngestion/getLinks",
  async () => await DataIngestionService.getLinks(),
);

export const dataIngestionSlice = createSlice({
  name: "dataIngestion",
  initialState,
  reducers: {
    setNotification(state, action: PayloadAction<Notification>) {
      state.notification = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(getFiles.pending, (state) => {
      state.files.isLoading = true;
    });
    builder.addCase(getFiles.fulfilled, (state, action) => {
      if (state.files.isLoading) {
        state.files.isLoading = false;
        state.files.data = action.payload;
        state.files.error = null;
      }
    });
    builder.addCase(getFiles.rejected, (state, action) => {
      if (state.files.isLoading) {
        state.files.isLoading = false;
        state.files.error = action.error;
        state.notification = {
          open: true,
          message: "Failed fetching files",
          severity: "error",
        };
      }
    });

    builder.addCase(getLinks.pending, (state) => {
      state.links.isLoading = true;
    });
    builder.addCase(getLinks.fulfilled, (state, action) => {
      if (state.links.isLoading) {
        state.links.isLoading = false;
        state.links.data = action.payload;
        state.links.error = null;
      }
    });
    builder.addCase(getLinks.rejected, (state, action) => {
      if (state.links.isLoading) {
        state.links.isLoading = false;
        state.links.error = action.error;
        state.notification = {
          open: true,
          message: "Failed fetching links",
          severity: "error",
        };
      }
    });
  },
});

export const { setNotification } = dataIngestionSlice.actions;

export const filesDataSelector = (state: RootState) =>
  state.dataIngestion.files.data;
export const filesDataIsLoadingSelector = (state: RootState) =>
  state.dataIngestion.files.isLoading;
export const filesDataErrorSelector = (state: RootState) =>
  state.dataIngestion.files.error;
export const linksDataSelector = (state: RootState) =>
  state.dataIngestion.links.data;
export const linksDataIsLoadingSelector = (state: RootState) =>
  state.dataIngestion.links.isLoading;
export const linksDataErrorSelector = (state: RootState) =>
  state.dataIngestion.links.error;
export const notificationSelector = (state: RootState) =>
  state.dataIngestion.notification;

export default dataIngestionSlice.reducer;
