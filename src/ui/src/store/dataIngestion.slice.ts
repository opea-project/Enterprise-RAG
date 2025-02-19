// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  createAsyncThunk,
  createSlice,
  SerializedError,
} from "@reduxjs/toolkit";

import DataIngestionService from "@/services/dataIngestionService";
import { RootState } from "@/store/index";
import { addNotification } from "@/store/notifications.slice";
import { FileDataItem, LinkDataItem } from "@/types/admin-panel/data-ingestion";

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
};

export const getFiles = createAsyncThunk(
  "dataIngestion/getFiles",
  async (_, { dispatch }) => {
    try {
      return await DataIngestionService.getFiles();
    } catch (error) {
      const errorMessage =
        error instanceof Error && error.name !== "SyntaxError"
          ? error.message
          : "Failed to fetch files";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    }
  },
);

export const getLinks = createAsyncThunk(
  "dataIngestion/getLinks",
  async (_, { dispatch }) => {
    try {
      return await DataIngestionService.getLinks();
    } catch (error) {
      const errorMessage =
        error instanceof Error && error.name !== "SyntaxError"
          ? error.message
          : "Failed to fetch links";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    }
  },
);

export const dataIngestionSlice = createSlice({
  name: "dataIngestion",
  initialState,
  reducers: {},
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
      }
    });
  },
});

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

export default dataIngestionSlice.reducer;
