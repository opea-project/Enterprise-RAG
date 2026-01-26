// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { RootState } from "@/store";

interface ViewNavigationState {
  lastSelectedChatId: string | null;
  lastSelectedAdminTab: string;
}

const initialState: ViewNavigationState = {
  lastSelectedChatId: null,
  lastSelectedAdminTab: "control-plane",
};

export const viewNavigationSlice = createSlice({
  name: "viewNavigation",
  initialState,
  reducers: {
    setLastSelectedChatId: (state, action: PayloadAction<string | null>) => {
      state.lastSelectedChatId = action.payload;
    },
    setLastSelectedAdminTab: (state, action: PayloadAction<string>) => {
      state.lastSelectedAdminTab = action.payload;
    },
    resetViewNavigationSlice: () => initialState,
  },
});

export const {
  setLastSelectedChatId,
  setLastSelectedAdminTab,
  resetViewNavigationSlice,
} = viewNavigationSlice.actions;

export const selectLastSelectedChatId = (state: RootState) =>
  state.viewNavigation.lastSelectedChatId;

export const selectLastSelectedAdminTab = (state: RootState) =>
  state.viewNavigation.lastSelectedAdminTab;

export default viewNavigationSlice.reducer;
