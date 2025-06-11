// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./index.scss";

import { StrictMode } from "react";
import { Container, createRoot } from "react-dom/client";

import App from "@/app";
import { keycloakService } from "@/lib/auth";

const renderApp = () => {
  const container = document.getElementById("root") as Container;
  const root = createRoot(container);

  root.render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
};

if (import.meta.env.PROD) {
  fetch("/config.json")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to fetch config.json: ${response.statusText}`);
      }

      return response.json();
    })
    .then((config) => {
      window.env = config;
      keycloakService.setup();
      keycloakService.init(renderApp);
    });
} else {
  keycloakService.setup();
  keycloakService.init(renderApp);
}
