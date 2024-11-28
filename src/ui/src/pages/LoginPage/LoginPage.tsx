// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LoginPage.scss";

import { Navigate } from "react-router-dom";

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
      <button className="login-page__button" onClick={keycloakService.login}>
        Login
      </button>
    </div>
  );
};

export default LoginPage;
