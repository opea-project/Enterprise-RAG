// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import {
  selectColorScheme,
  toggleColorScheme as toggleColorSchemeAction,
} from "@/components/ui/ColorSchemeSwitch/colorScheme.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const useColorScheme = () => {
  const dispatch = useAppDispatch();
  const colorScheme = useAppSelector(selectColorScheme);

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

export default useColorScheme;
