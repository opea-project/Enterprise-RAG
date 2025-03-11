// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import keycloak, {
  adminResourceRole,
  initOptions,
  loginOptions,
  minTokenValidity,
} from "@/lib/auth/config";

export const initializeKeycloak = async (onAuthenticated: () => void) => {
  try {
    const isAuthenticated = await keycloak.init(initOptions);
    if (isAuthenticated) {
      onAuthenticated();
    } else {
      redirectToLogin();
    }
  } catch (error) {
    console.error(error);
    redirectToLogin();
  }
};
export const redirectToLogin = () => keycloak.login(loginOptions);
export const redirectToLogout = () => keycloak.logout();
export const refreshToken = async () => {
  if (keycloak.authenticated) {
    try {
      await keycloak.updateToken(minTokenValidity);
    } catch (error) {
      console.error("An error occurred while refreshing the token:", error);
      console.error("Failed to refresh token. Logging out...");
      redirectToLogout();
    }
  } else {
    console.warn("User is not authenticated. Redirecting to login...");
    redirectToLogin();
  }
};

export const getToken = () => keycloak.token;
export const getUsername = () => keycloak.tokenParsed?.name;

export const isAdminUser = () => keycloak.hasResourceRole(adminResourceRole);
