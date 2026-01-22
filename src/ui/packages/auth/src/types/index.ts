// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  KeycloakConfig,
  KeycloakInitOptions,
  KeycloakLoginOptions,
} from "keycloak-js";

export interface KeycloakServiceConfig {
  keycloakConfig: KeycloakConfig;
  loginOptions?: KeycloakLoginOptions;
  adminResourceRole?: string;
  initOptions?: KeycloakInitOptions;
  minTokenValidity?: number;
  onRefreshTokenFailed?: () => void;
}
