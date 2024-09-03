// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createBrowserRouter } from "react-router-dom";

import PageLayout from "@/layout/PageLayout/PageLayout";
import AdminPanelPage from "@/pages/AdminPanelPage/AdminPanelPage";
import Chat from "@/pages/ChatPage/ChatPage";
import ErrorPage from "@/pages/ErrorPage/ErrorPage";
import LoginPage from "@/pages/LoginPage/LoginPage";
import ProtectedRoute from "@/router/ProtectedRoute";

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <PageLayout />
      </ProtectedRoute>
    ),
    errorElement: <ErrorPage />,
    children: [
      {
        path: "/chat",
        element: (
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        ),
      },
      {
        path: "/admin-panel",
        element: (
          <ProtectedRoute>
            <AdminPanelPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
]);

export default router;
