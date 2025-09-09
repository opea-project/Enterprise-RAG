// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  LoadingFallback,
  useColorScheme,
} from "@intel-enterprise-rag-ui/components";
import { RootLayout } from "@intel-enterprise-rag-ui/layouts";
import { lazy, Suspense } from "react";
import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom";

import ErrorRoute from "@/app/routes/error/ErrorRoute";
import ProtectedRoute from "@/components/ProtectedRoute/ProtectedRoute";
import { paths } from "@/config/paths";

const InitialChatRoute = lazy(
  () => import("@/app/routes/chat/InitialChatRoute"),
);
const ChatConversationRoute = lazy(
  () => import("@/app/routes/chat/ChatConversationRoute"),
);
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
    element: <RootLayout />,
    children: [
      {
        path: paths.chat,
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <InitialChatRoute />
          </Suspense>
        ),
      },
      {
        path: `${paths.chat}/:chatId`,
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <ChatConversationRoute />
          </Suspense>
        ),
      },
      {
        path: `${paths.adminPanel}/*`,
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
