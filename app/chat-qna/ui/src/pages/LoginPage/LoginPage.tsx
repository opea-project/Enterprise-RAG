// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LoginPage.scss";

import { useEffect } from "react";
import { Navigate } from "react-router-dom";

import keycloakService from "@/services/keycloakService";

const LoginPage = () => {
  const isUserLoggedIn = keycloakService.isLoggedIn();

  useEffect(() => {
    const theme = localStorage.getItem("theme");
    if (theme === "dark") {
      document.body.classList.add("dark");
    }
  }, []);

  return isUserLoggedIn ? (
    <Navigate to="/chat" />
  ) : (
    <div className="login-page">
      <p className="login-page-app-name">Enterprise RAG</p>
      <button onClick={keycloakService.login}>Login</button>
    </div>
  );
};

export default LoginPage;
