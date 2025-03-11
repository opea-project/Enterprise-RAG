// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  createAsyncThunk,
  createSlice,
  SerializedError,
} from "@reduxjs/toolkit";

import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { getFiles } from "@/features/admin-panel/data-ingestion/api/getFiles";
import { getLinks } from "@/features/admin-panel/data-ingestion/api/getLinks";
import {
  FileDataItem,
  LinkDataItem,
} from "@/features/admin-panel/data-ingestion/types";
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

export const fetchFiles = createAsyncThunk(
  "dataIngestion/fetchFiles",
  async (_, { dispatch }) => {
    try {
      return await getFiles();
    } catch (error) {
      const errorMessage =
        error instanceof Error && error.name !== "SyntaxError"
          ? error.message
          : "Failed to fetch files";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    }
  },
);

export const fetchLinks = createAsyncThunk(
  "dataIngestion/fetchLinks",
  async (_, { dispatch }) => {
    try {
      return await getLinks();
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
    builder.addCase(fetchFiles.pending, (state) => {
      state.files.isLoading = true;
    });
    builder.addCase(fetchFiles.fulfilled, (state, action) => {
      if (state.files.isLoading) {
        state.files.isLoading = false;
        state.files.data = action.payload;
        state.files.error = null;
      }
    });
    builder.addCase(fetchFiles.rejected, (state, action) => {
      if (state.files.isLoading) {
        state.files.isLoading = false;
        state.files.error = action.error;
      }
    });

    builder.addCase(fetchLinks.pending, (state) => {
      state.links.isLoading = true;
    });
    builder.addCase(fetchLinks.fulfilled, (state, action) => {
      if (state.links.isLoading) {
        state.links.isLoading = false;
        state.links.data = action.payload;
        state.links.error = null;
      }
    });
    builder.addCase(fetchLinks.rejected, (state, action) => {
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
