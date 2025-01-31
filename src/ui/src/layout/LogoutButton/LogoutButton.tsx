// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import IconButton from "@/components/shared/IconButton/IconButton";
import Tooltip from "@/components/shared/Tooltip/Tooltip";
import keycloakService from "@/services/keycloakService";

const LogoutButton = () => (
  <Tooltip text="Logout">
    <IconButton icon="logout" onClick={keycloakService.logout} />
  </Tooltip>
);

export default LogoutButton;
