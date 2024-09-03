// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PageLayout.scss";

import { Toolbar } from "@mui/material";
import { Outlet } from "react-router-dom";

import AppHeader from "@/layout/AppHeader/AppHeader";
import NavigationDrawer from "@/layout/NavigationDrawer/NavigationDrawer";

const PageLayout = () => (
  <>
    <AppHeader />
    <NavigationDrawer />
    <main className="main-outlet">
      {/* empty Toolbar to provide consistent top margin */}
      <Toolbar />
      <Outlet />
    </main>
  </>
);

export default PageLayout;
