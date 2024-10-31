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
const getTokenExpirationTime = () => keycloakClient.tokenParsed?.exp ?? 0;
const getTimeSkew = () => keycloakClient.timeSkew ?? 0;
const getTokenValidityTime = () => {
  const tokenExpirationTime = getTokenExpirationTime();
  const currentTime = new Date().getTime() / 1000;
  const timeSkew = getTimeSkew();
  return Math.round(tokenExpirationTime + timeSkew - currentTime);
};

const refreshToken = () => {
  keycloakClient
    .updateToken(minTokenValidity)
    .then((refreshed) => {
      if (refreshed) {
        const token = keycloakService.getToken();
        if (typeof token === "string") {
          sessionStorage.setItem("token", token);
        }
        console.info("Token refreshed");
      } else {
        console.info(
          `Token not refreshed, valid for ${getTokenValidityTime()} seconds`,
        );
      }
    })
    .catch(() => {
      console.error("Failed to refresh token. Logging out...");
      logout();
    });
};

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
