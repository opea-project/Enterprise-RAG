// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LoginPage.scss";

import { Button, Typography } from "@mui/material";
import { Navigate } from "react-router-dom";

import keycloakService from "@/services/keycloakService";

const LoginPage = () => {
  const isUserLoggedIn = keycloakService.isLoggedIn();

  return isUserLoggedIn ? (
    <Navigate to="/chat" />
  ) : (
    <div className="login-page">
      <Typography variant="login-page-app-name">Enterprise RAG</Typography>
      <Button size="large" onClick={keycloakService.login}>
        Login
      </Button>
    </div>
  );
};

export default LoginPage;
