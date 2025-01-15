// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { RouterProvider } from "react-router-dom";

import useSessionIdleTimeout from "@/auth/useSessionIdleTimeout";
import useTokenRefresh from "@/auth/useTokenRefresh";
import router from "@/router";
import useCheckChatPipelineConfig from "@/utils/hooks/useCheckChatPipelineConfig";

const App = () => {
  useTokenRefresh();
  useCheckChatPipelineConfig();
  useSessionIdleTimeout();

  return <RouterProvider router={router} />;
};

export default App;
