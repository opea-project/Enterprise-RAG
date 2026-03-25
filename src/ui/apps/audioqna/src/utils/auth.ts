// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  KeycloakService,
  KeycloakServiceConfig,
} from "@intel-enterprise-rag-ui/auth";

import { paths } from "@/config/paths";
import { getAudioQnAAppEnv } from "@/utils";
import { onRefreshTokenFailed } from "@/utils/api";

export const keycloakService = new KeycloakService();

export const initializeKeycloak = (onInitialized: () => void) => {
  const config: KeycloakServiceConfig = {
    keycloakConfig: {
      url: getAudioQnAAppEnv("KEYCLOAK_URL"),
      realm: getAudioQnAAppEnv("KEYCLOAK_REALM"),
      clientId: getAudioQnAAppEnv("KEYCLOAK_CLIENT_ID"),
    },
    adminResourceRole: getAudioQnAAppEnv("ADMIN_RESOURCE_ROLE"),
    maintainerResourceRole: getAudioQnAAppEnv("MAINTAINER_RESOURCE_ROLE"),
    loginOptions: {
      redirectUri: location.origin + paths.chat,
    },
    onRefreshTokenFailed,
  };
  keycloakService.setup(config);
  keycloakService.init(onInitialized);
};
