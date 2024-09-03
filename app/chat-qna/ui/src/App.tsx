// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ThemeProvider } from "@mui/material";
import { RouterProvider } from "react-router-dom";

import router from "@/router";
import theme from "@/theme";

const App = () => (
  <ThemeProvider theme={theme}>
    <RouterProvider router={router} />
  </ThemeProvider>
);

export default App;
