// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Keycloak, { KeycloakConfig, KeycloakInitOptions } from "keycloak-js";

import { paths } from "@/config/paths";

const config: KeycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL,
  realm: import.meta.env.VITE_KEYCLOAK_REALM,
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
};

export const initOptions: KeycloakInitOptions = {
  onLoad: "check-sso",
  checkLoginIframe: false,
};

export const loginOptions = { redirectUri: location.origin + paths.chat };

export const minTokenValidity = 30; // seconds, 5 - default value

export const adminResourceRole = import.meta.env.VITE_ADMIN_RESOURCE_ROLE;

const keycloak = new Keycloak(config);

export default keycloak;
