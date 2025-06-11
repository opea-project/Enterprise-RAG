// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Keycloak, { KeycloakConfig } from "keycloak-js";

import { initOptions, loginOptions, minTokenValidity } from "@/lib/auth/config";
import { getAppEnv } from "@/utils";

class KeycloakService {
  private keycloak: Keycloak | null = null;
  private adminResourceRole: string = "";

  constructor() {}

  setup() {
    try {
      const config: KeycloakConfig = {
        url: getAppEnv("KEYCLOAK_URL"),
        realm: getAppEnv("KEYCLOAK_REALM"),
        clientId: getAppEnv("KEYCLOAK_CLIENT_ID"),
      };
      this.adminResourceRole = getAppEnv("ADMIN_RESOURCE_ROLE");
      this.keycloak = new Keycloak(config);
    } catch (e) {
      console.error("Failed to initialize Keycloak", e);
    }
  }

  init = async (onAuthenticated: () => void) => {
    try {
      const isAuthenticated = await this.keycloak?.init(initOptions);
      if (isAuthenticated) {
        onAuthenticated();
      } else {
        this.keycloak?.login(loginOptions);
      }
    } catch (error) {
      console.error(error);
      this.keycloak?.login(loginOptions);
    }
  };
  redirectToLogin = () => this.keycloak?.login(loginOptions);
  redirectToLogout = () => this.keycloak?.logout();
  refreshToken = async (onRefreshTokenFailed: () => void) => {
    if (this.keycloak?.authenticated) {
      try {
        await this.keycloak.updateToken(minTokenValidity);
      } catch (error) {
        console.error("An error occurred while refreshing the token:", error);
        console.error("Failed to refresh token. Logging out...");
        onRefreshTokenFailed();
      }
    } else {
      console.warn("User is not authenticated. Redirecting to login...");
      this.keycloak?.login(loginOptions);
    }
  };

  getToken = () => this.keycloak?.token ?? "";
  getUsername = () => this.keycloak?.tokenParsed?.name;
  isAdminUser = () => this.keycloak?.hasResourceRole(this.adminResourceRole);
}

export const keycloakService = new KeycloakService();
