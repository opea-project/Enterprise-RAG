// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import MainPage from "@/app/MainPage";
import AppProvider from "@/app/provider";

const App = () => (
  <AppProvider>
    <MainPage />
  </AppProvider>
);

export default App;
