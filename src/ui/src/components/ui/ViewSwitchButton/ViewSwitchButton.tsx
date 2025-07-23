// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useLocation, useNavigate } from "react-router-dom";

import { IconName } from "@/components/icons";
import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { paths } from "@/config/paths";
import { keycloakService } from "@/lib/auth";

const options = {
  chat: {
    tooltip: "Switch to Admin Panel",
    routePath: paths.adminPanel,
    icon: "admin-panel" as IconName,
    ariaLabel: "Switch to Admin Panel",
  },
  "admin-panel": {
    tooltip: "Switch to Chat",
    routePath: paths.chat,
    icon: "chat" as IconName,
    ariaLabel: "Switch to Chat",
  },
} as const;

const ViewSwitchButton = () => {
  const navigate = useNavigate();
  const location = useLocation();

  if (!keycloakService.isAdminUser()) {
    return null;
  }

  const isChatPage = location.pathname.startsWith(paths.chat);
  const isAdminPanelPage = location.pathname.startsWith(paths.adminPanel);

  if (!isChatPage && !isAdminPanelPage) {
    return null;
  }

  const currentView = isChatPage ? "chat" : "admin-panel";

  return (
    <Tooltip
      title={options[currentView].tooltip}
      trigger={
        <IconButton
          icon={options[currentView].icon}
          aria-label={options[currentView].ariaLabel}
          onPress={() => navigate(options[currentView].routePath)}
        />
      }
      placement="bottom"
    />
  );
};

export default ViewSwitchButton;
