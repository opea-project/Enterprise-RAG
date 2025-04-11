// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import { refreshToken } from "@/lib/auth";
import { onRefreshTokenFailed } from "@/utils/api";

const useTokenRefresh = () => {
  useEffect(() => {
    const refreshTokenInterval = setInterval(() => {
      refreshToken(onRefreshTokenFailed);
    }, 60000);
    return () => clearInterval(refreshTokenInterval);
  }, []);
};

export default useTokenRefresh;
