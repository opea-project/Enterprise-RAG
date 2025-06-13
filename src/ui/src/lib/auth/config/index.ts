// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { KeycloakInitOptions } from "keycloak-js";

import { paths } from "@/config/paths";

export const initOptions: KeycloakInitOptions = {
  onLoad: "check-sso",
  checkLoginIframe: false,
};

export const loginOptions = { redirectUri: location.origin + paths.chat };

export const minTokenValidity = 30; // seconds, 5 - default value
