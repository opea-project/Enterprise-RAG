// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PropsWithChildren } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { paths } from "@/config/paths";
import { isAdminUser } from "@/lib/auth";

const ProtectedRoute = ({ children }: PropsWithChildren) => {
  const location = useLocation();
  const isAdminPanelRoute = location.pathname === paths.adminPanel;

  if (isAdminPanelRoute && !isAdminUser()) {
    return <Navigate to={paths.chat} replace />;
  } else {
    return children;
  }
};

export default ProtectedRoute;
