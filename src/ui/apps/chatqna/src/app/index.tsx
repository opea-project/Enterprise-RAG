// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTokenRefresh } from "@intel-enterprise-rag-ui/auth";

import AppProvider from "@/app/provider";
import AppRouter from "@/app/router";
import { keycloakService } from "@/utils/auth";

const App = () => {
  useTokenRefresh(keycloakService);

  return (
    <AppProvider>
      <AppRouter />
    </AppProvider>
  );
};

export default App;