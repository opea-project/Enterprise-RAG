// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { v4 as uuid } from "uuid";

import { RootState } from "@/store";
import { HistoryItemData } from "@/types";

interface HistoryState {
  items: HistoryItemData[];
}

const initialState: HistoryState = {
  items: [],
};

const historySlice = createSlice({
  name: "history",
  initialState,
  reducers: {
    addHistoryItem: (
      state,
      action: PayloadAction<Omit<HistoryItemData, "id" | "timestamp">>,
    ) => {
      state.items.push({
        ...action.payload,
        timestamp: new Date().toLocaleString(),
        id: uuid(),
      });
    },
    removeHistoryItem: (state, action: PayloadAction<string>) => {
      const idToRemove = action.payload;
      state.items = state.items.filter((item) => item.id !== idToRemove);
    },
    renameHistoryItem: (
      state,
      action: PayloadAction<{ id: string; newName: string }>,
    ) => {
      const { id, newName } = action.payload;
      const item = state.items.find((item) => item.id === id);
      if (item) {
        item.title = newName;
      }
    },
  },
});

export const { addHistoryItem, removeHistoryItem, renameHistoryItem } =
  historySlice.actions;

export const selectHistoryItems = (state: RootState) => state.history.items;

export default historySlice.reducer;
