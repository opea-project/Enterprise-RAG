// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { keycloakService } from "@/utils/auth";

const onRefreshTokenFailed = () => {
  keycloakService.redirectToLogout();
};

export { onRefreshTokenFailed };
