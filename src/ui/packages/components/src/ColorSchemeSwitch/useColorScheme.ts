// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

import {
  selectColorScheme,
  toggleColorScheme as toggleColorSchemeAction,
} from "@/ColorSchemeSwitch/colorScheme.slice";

/**
 * Custom React hook for managing and toggling the application's color scheme (light/dark).
 * Adds/removes the 'dark' class on the document body and persists the scheme in localStorage.
 * Returns the current color scheme and a function to toggle it.
 *
 * @returns {{ colorScheme: string, toggleColorScheme: () => void }}
 */
export const useColorScheme = () => {
  const dispatch = useDispatch();
  const colorScheme = useSelector(selectColorScheme);

  useEffect(() => {
    if (colorScheme === "dark") {
      document.body.classList.add("dark");
    } else {
      document.body.classList.remove("dark");
    }
    localStorage.setItem("colorScheme", colorScheme);
  }, [colorScheme]);

  const toggleColorScheme = () => {
    dispatch(toggleColorSchemeAction());
  };

  return { colorScheme, toggleColorScheme };
};
