// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { redirectToLogout } from "@/lib/auth";

const LogoutButton = () => (
  <Tooltip text="Logout">
    <IconButton icon="logout" onClick={redirectToLogout} />
  </Tooltip>
);

export default LogoutButton;
