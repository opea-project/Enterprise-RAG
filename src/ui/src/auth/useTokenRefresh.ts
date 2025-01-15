// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import keycloakService from "@/services/keycloakService";

const REFRESH_TOKEN_INTERVAL = 1000 * keycloakService.minTokenValidity;

const useTokenRefresh = () => {
  useEffect(() => {
    const refreshTokenInterval = setInterval(() => {
      keycloakService.refreshToken();
    }, REFRESH_TOKEN_INTERVAL);

    return () => clearInterval(refreshTokenInterval);
  }, []);
};

export default useTokenRefresh;
