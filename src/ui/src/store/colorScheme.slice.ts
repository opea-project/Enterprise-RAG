// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice } from "@reduxjs/toolkit";

import { RootState } from "@/store";

type ColorScheme = "light" | "dark";

const getColorScheme = (): ColorScheme => {
  const storedColorScheme = localStorage.getItem("colorScheme");
  if (
    storedColorScheme !== null &&
    ["light", "dark"].includes(storedColorScheme)
  ) {
    return storedColorScheme as ColorScheme;
  }

  const darkSchemeMediaQuery = window.matchMedia(
    "(prefers-color-scheme: dark)",
  );
  const prefersDarkSchemeMediaQuery = darkSchemeMediaQuery.matches;
  const colorScheme = prefersDarkSchemeMediaQuery ? "dark" : "light";
  return colorScheme;
};

interface ColorSchemeState {
  colorScheme: ColorScheme;
}

const initialState: ColorSchemeState = {
  colorScheme: getColorScheme(),
};

const colorSchemeSlice = createSlice({
  name: "colorScheme",
  initialState,
  reducers: {
    toggleColorScheme: (state) => {
      state.colorScheme = state.colorScheme === "light" ? "dark" : "light";
    },
  },
});

export const { toggleColorScheme } = colorSchemeSlice.actions;

export const selectColorScheme = (state: RootState) =>
  state.colorScheme.colorScheme;

export default colorSchemeSlice.reducer;
