// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "../index.scss";

import { StrictMode } from "react";
import { Container, createRoot } from "react-dom/client";
import { Provider } from "react-redux";

import App from "@/App";
import LoginPage from "@/pages/LoginPage/LoginPage";
import keycloakService from "@/services/keycloakService";
import { store } from "@/store";

keycloakService.initKeycloak((isAuthenticated) => {
  const rootElement = document.getElementById("root") as Container;

  createRoot(rootElement).render(
    <StrictMode>
      <Provider store={store}>
        {isAuthenticated ? <App /> : <LoginPage />}
      </Provider>
    </StrictMode>,
  );
});
