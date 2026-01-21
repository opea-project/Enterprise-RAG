// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  KeycloakService,
  KeycloakServiceConfig,
} from "@intel-enterprise-rag-ui/auth";

import { paths } from "@/config/paths";
import { getChatQnAAppEnv } from "@/utils";
import { onRefreshTokenFailed } from "@/utils/api";

export const keycloakService = new KeycloakService();

export const initializeKeycloak = (onInitialized: () => void) => {
  const config: KeycloakServiceConfig = {
    keycloakConfig: {
      url: getChatQnAAppEnv("KEYCLOAK_URL"),
      realm: getChatQnAAppEnv("KEYCLOAK_REALM"),
      clientId: getChatQnAAppEnv("KEYCLOAK_CLIENT_ID"),
    },
    adminResourceRole: getChatQnAAppEnv("ADMIN_RESOURCE_ROLE"),
    loginOptions: {
      redirectUri: location.origin + paths.chat,
    },
    onRefreshTokenFailed,
  };
  keycloakService.setup(config);
  keycloakService.init(onInitialized);
};
