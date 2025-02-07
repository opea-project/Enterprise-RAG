// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LoginPage.scss";

import { Navigate } from "react-router-dom";

import Button from "@/components/shared/Button/Button";
import keycloakService from "@/services/keycloakService";
import useColorScheme from "@/utils/hooks/useColorScheme";

const LoginPage = () => {
  const isUserLoggedIn = keycloakService.isLoggedIn();

  useColorScheme();

  return isUserLoggedIn ? (
    <Navigate to="/chat" />
  ) : (
    <div className="login-page">
      <p className="login-page__app-name">Intel AI&reg; for Enterprise RAG</p>
      <Button onClick={keycloakService.login}>Login</Button>
    </div>
  );
};

export default LoginPage;
