// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { redirectToLogout } from "@/lib/auth";
import { resetStore } from "@/store/utils";

const LogoutButton = () => {
  const handleLogout = () => {
    resetStore();
    redirectToLogout();
  };

  return (
    <Tooltip
      title="Logout"
      trigger={<IconButton icon="logout" onClick={handleLogout} />}
      placement="bottom"
    />
  );
};
export default LogoutButton;
