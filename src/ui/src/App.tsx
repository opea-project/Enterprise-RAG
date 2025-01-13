// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { RouterProvider } from "react-router-dom";

import useTokenRefresh from "@/auth/useTokenRefresh";
import router from "@/router";

const App = () => {
  useTokenRefresh();
  return <RouterProvider router={router} />;
};

export default App;
