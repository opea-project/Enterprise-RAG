// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice } from "@reduxjs/toolkit";

import { RootState } from "@/store";

interface ChatSideMenusState {
  isChatHistorySideMenuOpen: boolean;
}

const initialState: ChatSideMenusState = {
  isChatHistorySideMenuOpen: false,
};

const chatSideMenusSlice = createSlice({
  name: "chatSideMenus",
  initialState,
  reducers: {
    openChatHistorySideMenu: (state) => {
      state.isChatHistorySideMenuOpen = true;
    },
    closeChatHistorySideMenu: (state) => {
      state.isChatHistorySideMenuOpen = false;
    },
    toggleChatHistorySideMenu: (state) => {
      state.isChatHistorySideMenuOpen = !state.isChatHistorySideMenuOpen;
    },
    resetChatSideMenusSlice: () => initialState,
  },
});

export const {
  openChatHistorySideMenu,
  closeChatHistorySideMenu,
  toggleChatHistorySideMenu,
  resetChatSideMenusSlice,
} = chatSideMenusSlice.actions;

export const selectIsChatHistorySideMenuOpen = (state: RootState) =>
  state.chatSideMenus.isChatHistorySideMenuOpen;

export default chatSideMenusSlice.reducer;
