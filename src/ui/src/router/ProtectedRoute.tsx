// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PropsWithChildren } from "react";
import { Navigate, useLocation } from "react-router-dom";

import keycloakService from "@/services/keycloakService";

const ProtectedRoute = ({ children }: PropsWithChildren) => {
  const location = useLocation();

  const isRootRoute = location.pathname === "/";
  const isAdminPanelRoute = location.pathname === "/admin-panel";

  const isUserLoggedIn = keycloakService.isLoggedIn();
  const isAdmin = keycloakService.isAdmin();

  let route;
  if (isUserLoggedIn) {
    if (isRootRoute || (isAdminPanelRoute && !isAdmin)) {
      route = <Navigate to="/chat" />;
    } else {
      route = children;
    }
  } else {
    route = <Navigate to="/login" />;
  }

  return route;
};

export default ProtectedRoute;
