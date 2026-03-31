// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PropsWithChildren } from "react";
import { Navigate } from "react-router-dom";

import { paths } from "@/config/paths";
import { getAudioQnAAppEnv } from "@/utils";
import { keycloakService } from "@/utils/auth";

const AccessGuard = ({ children }: PropsWithChildren) => {
  const userRole = getAudioQnAAppEnv("USER_RESOURCE_ROLE");

  const hasAccess =
    keycloakService.isAdminUser() ||
    (userRole && keycloakService.hasResourceRole(userRole));

  if (!hasAccess) {
    return <Navigate to={paths.unauthorized} replace />;
  }

  return children;
};

export default AccessGuard;
