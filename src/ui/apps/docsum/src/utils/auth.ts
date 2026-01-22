// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  KeycloakService,
  KeycloakServiceConfig,
} from "@intel-enterprise-rag-ui/auth";

import { getDocSumAppEnv } from "@/utils";
import { onRefreshTokenFailed } from "@/utils/api";

export const keycloakService = new KeycloakService();

export const initializeKeycloak = (onInitialized: () => void) => {
  const config: KeycloakServiceConfig = {
    keycloakConfig: {
      url: getDocSumAppEnv("KEYCLOAK_URL"),
      realm: getDocSumAppEnv("KEYCLOAK_REALM"),
      clientId: getDocSumAppEnv("KEYCLOAK_CLIENT_ID"),
    },
    adminResourceRole: getDocSumAppEnv("ADMIN_RESOURCE_ROLE"),
    loginOptions: {
      redirectUri: location.origin,
    },
    onRefreshTokenFailed,
  };
  keycloakService.setup(config);
  keycloakService.init(onInitialized);
};
