// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";

import PageLayout from "@/layout/PageLayout/PageLayout";
import AdminPanelPage from "@/pages/AdminPanelPage";
import ChatPage from "@/pages/ChatPage";
import ErrorPage from "@/pages/ErrorPage";
import LoginPage from "@/pages/LoginPage";
import ProtectedRoute from "@/router/ProtectedRoute";

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <PageLayout />
      </ProtectedRoute>
    ),
    errorElement: (
      <Suspense>
        <ErrorPage />
      </Suspense>
    ),
    children: [
      {
        path: "/chat",
        element: (
          <ProtectedRoute>
            <Suspense>
              <ChatPage />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: "/admin-panel",
        element: (
          <ProtectedRoute>
            <Suspense>
              <AdminPanelPage />
            </Suspense>
          </ProtectedRoute>
        ),
      },
    ],
  },
  {
    path: "/login",
    element: (
      <Suspense>
        <LoginPage />
      </Suspense>
    ),
  },
]);

export default router;
