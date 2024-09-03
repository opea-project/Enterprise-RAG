// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Keycloak, { KeycloakConfig, KeycloakInitOptions } from "keycloak-js";

const config: KeycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL,
  realm: import.meta.env.VITE_KEYCLOAK_REALM,
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
};

const initOptions: KeycloakInitOptions = {
  onLoad: "check-sso",
  checkLoginIframe: false,
};

const loginOptions = { redirectUri: location.origin + "/chat" };
const logoutOptions = { redirectUri: location.origin + "/login" };

const minTokenValidity = 5; // seconds, 5 - default value

const adminResourceRole = import.meta.env.VITE_ADMIN_RESOURCE_ROLE;

const keycloakClient = new Keycloak(config);

const initKeycloak = (onAuthenticatedCallback: () => void) => {
  keycloakClient
    .init(initOptions)
    .then((isAuthenticated) => {
      if (!isAuthenticated) {
        console.log("User not authenticated!");
      }
      onAuthenticatedCallback();
    })
    .catch((error) => console.error(error));
};

const login = () => keycloakClient.login(loginOptions);
const logout = () => keycloakClient.logout(logoutOptions);
const isLoggedIn = () => !!keycloakClient.token;

const getToken = () => keycloakClient.token;
const getTokenParsed = () => keycloakClient.tokenParsed;
const refreshToken = (onRefreshCallback: () => void) =>
  keycloakClient
    .updateToken(minTokenValidity)
    .then(onRefreshCallback)
    .catch(login);

const getUsername = () => keycloakClient.tokenParsed?.name;
const hasRole = (role: string) => keycloakClient.hasRealmRole(role);
const hasResourceAccessRole = (role: string) =>
  keycloakClient.hasResourceRole(role);
const isAdmin = () => keycloakService.hasResourceAccessRole(adminResourceRole);

const keycloakService = {
  initKeycloak,
  login,
  logout,
  isLoggedIn,
  getToken,
  getTokenParsed,
  refreshToken,
  getUsername,
  hasRole,
  hasResourceAccessRole,
  isAdmin,
};

export default keycloakService;
