// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import { KeycloakService } from "@/service/keycloak";

/**
 * Custom React hook to periodically refresh the Keycloak token.
 * @param {KeycloakService} keycloakService - Instance of KeycloakService to refresh the token.
 * @param {number} [intervalMs=60000] - Interval in milliseconds for refreshing the token. Set to 60000 (1 minute) by default.
 */
export const useTokenRefresh = (
  keycloakService: KeycloakService,
  intervalMs: number = 60000,
) => {
  useEffect(() => {
    const refreshTokenInterval = setInterval(() => {
      keycloakService.refreshToken();
    }, intervalMs);
    return () => clearInterval(refreshTokenInterval);
  }, [keycloakService, intervalMs]);
};
