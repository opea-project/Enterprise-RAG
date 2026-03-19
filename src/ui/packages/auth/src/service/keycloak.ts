// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Keycloak, { KeycloakLoginOptions } from "keycloak-js";

import { KeycloakServiceConfig } from "@/types";

/**
 * Service class for handling Keycloak authentication and token management.
 */
export class KeycloakService {
  private keycloak: Keycloak | null = null;
  private adminResourceRole: string = "";
  private loginOptions: KeycloakLoginOptions = {};
  private config?: KeycloakServiceConfig;
  private minTokenValidity: number = 30;
  private onRefreshTokenFailed?: () => void;

  constructor() {}

  /**
   * Sets up the KeycloakService with configuration.
   * @param {KeycloakServiceConfig} config - Configuration object for KeycloakService.
   */
  setup(config: KeycloakServiceConfig) {
    this.config = config;
    this.loginOptions = config.loginOptions || {};
    this.adminResourceRole = config.adminResourceRole ?? "";
    this.minTokenValidity = config.minTokenValidity ?? 30;
    this.onRefreshTokenFailed = config.onRefreshTokenFailed;

    try {
      this.keycloak = new Keycloak(config.keycloakConfig);
    } catch (e) {
      console.error("Failed to initialize Keycloak", e);
    }
  }

  /**
   * Initializes Keycloak and handles authentication.
   * @param {() => void} onAuthenticated - Callback when authentication succeeds.
   * @returns {Promise<void>}
   */
  init = async (onAuthenticated: () => void) => {
    if (!this.config) {
      throw new Error("KeycloakService not configured. Call setup() first.");
    }
    try {
      const isAuthenticated = await this.keycloak?.init({
        onLoad: "check-sso",
        checkLoginIframe: false,
      });
      if (isAuthenticated) {
        onAuthenticated();
      } else {
        this.keycloak?.login(this.loginOptions);
      }
    } catch (error) {
      console.error(error);
      this.keycloak?.login(this.loginOptions);
    }
  };

  /**
   * Redirects the user to the Keycloak login page.
   * @returns {Promise<void>|void}
   */
  redirectToLogin = () => this.keycloak?.login(this.loginOptions);

  /**
   * Redirects the user to the Keycloak logout page.
   * @returns {Promise<void>|void}
   */
  redirectToLogout = () => this.keycloak?.logout();

  /**
   * Attempts to refresh the Keycloak token. If not authenticated, redirects to login.
   * Calls onRefreshTokenFailed if token refresh fails.
   * @returns {Promise<void>|void}
   */
  refreshToken = async () => {
    if (this.keycloak?.authenticated) {
      try {
        await this.keycloak.updateToken(this.minTokenValidity);
      } catch (error) {
        console.error("An error occurred while refreshing the token:", error);
        if (this.onRefreshTokenFailed) {
          this.onRefreshTokenFailed();
        }
      }
    } else {
      console.warn("User is not authenticated. Redirecting to login...");
      this.keycloak?.login(this.loginOptions);
    }
  };

  /**
   * Returns the current Keycloak token string.
   * @returns {string} The token, or an empty string if not available.
   */
  getToken = () => this.keycloak?.token ?? "";

  /**
   * Returns the username from the parsed Keycloak token.
   * @returns {string|undefined} The username, if available.
   */
  getUsername = () => this.keycloak?.tokenParsed?.name;

  /**
   * Checks if the current user has the admin resource role.
   * @returns {boolean|undefined} True if user is admin, otherwise false or undefined.
   */
  isAdminUser = () =>
    this.adminResourceRole &&
    this.keycloak?.hasResourceRole(this.adminResourceRole);
}
