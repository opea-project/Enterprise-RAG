// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { lazy, Suspense } from "react";
import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom";

import ErrorRoute from "@/app/routes/error/ErrorRoute";
import PageLayout from "@/components/layouts/PageLayout/PageLayout";
import LoadingFallback from "@/components/ui/LoadingFallback/LoadingFallback";
import { paths } from "@/config/paths";
import useColorScheme from "@/hooks/useColorScheme";
import ProtectedRoute from "@/lib/auth/components/ProtectedRoute";

const ChatRoute = lazy(() => import("@/app/routes/chat/ChatRoute"));
const AdminPanelRoute = lazy(
  () => import("@/app/routes/admin-panel/AdminPanelRoute"),
);

const router = createBrowserRouter([
  {
    path: paths.root,
    element: <Navigate to={paths.chat} replace />,
    errorElement: <ErrorRoute />,
  },
  {
    element: <PageLayout />,
    children: [
      {
        path: paths.chat,
        element: (
          <ProtectedRoute>
            <Suspense fallback={<LoadingFallback />}>
              <ChatRoute />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      {
        path: paths.adminPanel,
        element: (
          <ProtectedRoute>
            <Suspense fallback={<LoadingFallback />}>
              <AdminPanelRoute />
            </Suspense>
          </ProtectedRoute>
        ),
      },
      { path: "*", element: <ErrorRoute /> },
    ],
  },
]);

const AppRouter = () => {
  // useColorScheme hook used here to provide color scheme for the app and LoadingFallback component
  useColorScheme();

  return <RouterProvider router={router} />;
};

export default AppRouter;
