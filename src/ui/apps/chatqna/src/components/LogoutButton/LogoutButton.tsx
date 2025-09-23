// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconButton, Tooltip } from "@intel-enterprise-rag-ui/components";

import { resetStore } from "@/store/utils";
import { keycloakService } from "@/utils/auth";

export const LogoutButton = () => (
  <Tooltip
    title="Logout"
    trigger={
      <IconButton
        icon="logout"
        aria-label="Logout"
        onPress={() => {
          resetStore();
          keycloakService.redirectToLogout();
        }}
      />
    }
    placement="bottom"
  />
);
