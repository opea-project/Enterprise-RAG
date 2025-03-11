// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "@fontsource/inter";
import "@fontsource/inter/100.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/900.css";
import "./index.scss";

import { StrictMode } from "react";
import { Container, createRoot } from "react-dom/client";

import App from "@/app";
import { initializeKeycloak } from "@/lib/auth";

initializeKeycloak(() => {
  const container = document.getElementById("root") as Container;
  const root = createRoot(container);

  root.render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
});
