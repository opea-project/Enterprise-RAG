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

const minTokenValidity = 60; // seconds, 5 - default value

const adminResourceRole = import.meta.env.VITE_ADMIN_RESOURCE_ROLE;

const keycloak = new Keycloak(config);

const initKeycloak = (
  onAuthenticatedCallback: (isAuthenticated: boolean) => void,
) => {
  keycloak
    .init(initOptions)
    .then(onAuthenticatedCallback)
    .catch((error) => console.error(error));
};

const login = () => keycloak.login(loginOptions);
const logout = () => keycloak.logout(logoutOptions);
const isLoggedIn = () => !!keycloak.token;

const getToken = () => keycloak.token;
const getTokenParsed = () => keycloak.tokenParsed;
const getTokenExpirationTime = () => keycloak.tokenParsed?.exp ?? 0;
const getTimeSkew = () => keycloak.timeSkew ?? 0;
const getTokenValidityTime = () => {
  const tokenExpirationTime = getTokenExpirationTime();
  const currentTime = new Date().getTime() / 1000;
  const timeSkew = getTimeSkew();
  return Math.round(tokenExpirationTime + timeSkew - currentTime);
};

const refreshToken = async () => {
  await keycloak.updateToken(minTokenValidity).catch(() => {
    console.error("Failed to refresh token. Logging out...");
    logout();
  });
};

const getUsername = () => keycloak.tokenParsed?.name;
const hasRole = (role: string) => keycloak.hasRealmRole(role);
const hasResourceAccessRole = (role: string) => keycloak.hasResourceRole(role);
const isAdmin = () => keycloakService.hasResourceAccessRole(adminResourceRole);

const keycloakService = {
  initKeycloak,
  login,
  logout,
  isLoggedIn,
  getToken,
  getTokenParsed,
  getTokenValidityTime,
  refreshToken,
  getUsername,
  hasRole,
  hasResourceAccessRole,
  isAdmin,
  minTokenValidity,
};

export default keycloakService;
