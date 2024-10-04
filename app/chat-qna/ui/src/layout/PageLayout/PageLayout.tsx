// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PageLayout.scss";

import { Outlet } from "react-router-dom";

import AppHeader from "@/layout/AppHeader/AppHeader";

const PageLayout = () => (
  <div className="layout-root">
    <div className="content">
      <AppHeader />
      <main className="main-outlet">
        <Outlet />
      </main>
    </div>
  </div>
);

export default PageLayout;
