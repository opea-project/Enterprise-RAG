// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice } from "@reduxjs/toolkit";

export interface ChatSideMenuState {
  isChatSideMenuOpen: boolean;
}

const initialState: ChatSideMenuState = {
  isChatSideMenuOpen: false,
};

const chatSideMenuSlice = createSlice({
  name: "chatSideMenu",
  initialState,
  reducers: {
    toggleChatSideMenu: (state) => {
      state.isChatSideMenuOpen = !state.isChatSideMenuOpen;
    },
    resetChatSideMenuSlice: () => initialState,
  },
});

export const { toggleChatSideMenu, resetChatSideMenuSlice } =
  chatSideMenuSlice.actions;

export const selectIsChatSideMenuOpen = (state: {
  chatSideMenu: ChatSideMenuState;
}) => state.chatSideMenu.isChatSideMenuOpen;

export const chatSideMenuReducer = chatSideMenuSlice.reducer;
