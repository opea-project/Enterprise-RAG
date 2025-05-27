// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Outlet } from "react-router-dom";

const RootLayout = () => (
  <div className="h-screen w-screen">
    <Outlet />
  </div>
);

export default RootLayout;
