// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import AppProvider from "@/app/provider";
import AppRouter from "@/app/router";
import useTokenRefresh from "@/lib/auth/hooks/useTokenRefresh";

const App = () => {
  useTokenRefresh();

  return (
    <AppProvider>
      <AppRouter />
    </AppProvider>
  );
};

export default App;
