// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import keycloakService from "@/services/keycloakService";

const useTokenRefresh = () => {
  useEffect(() => {
    const refreshToken = () => {
      keycloakService.refreshToken();
    };

    const intervalId = setInterval(refreshToken, 1000 * 55);

    return () => clearInterval(intervalId);
  }, []);
};

export default useTokenRefresh;
