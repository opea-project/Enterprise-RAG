// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { keycloakService } from "@/lib/auth";
import { resetStore } from "@/store/utils";

const LogoutButton = () => {
  const handlePress = () => {
    resetStore();
    keycloakService.redirectToLogout();
  };

  return (
    <Tooltip
      title="Logout"
      trigger={
        <IconButton icon="logout" aria-label="Logout" onPress={handlePress} />
      }
      placement="bottom"
    />
  );
};
export default LogoutButton;
