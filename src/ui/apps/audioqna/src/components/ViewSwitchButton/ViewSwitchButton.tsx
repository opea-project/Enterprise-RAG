// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconButton, Tooltip } from "@intel-enterprise-rag-ui/components";
import { IconName } from "@intel-enterprise-rag-ui/icons";
import { useLocation, useNavigate } from "react-router-dom";

import { paths } from "@/config/paths";
import { useAppSelector } from "@/store/hooks";
import {
  selectLastSelectedAdminTab,
  selectLastSelectedChatId,
} from "@/store/viewNavigation.slice";
import { keycloakService } from "@/utils/auth";

const options = {
  chat: {
    tooltip: "Switch to Admin Panel",
    routePath: paths.adminPanel,
    icon: "admin-panel" as IconName,
    ariaLabel: "Switch to Admin Panel",
    dataTestId: "view-switch-btn--to-admin-panel",
  },
  "admin-panel": {
    tooltip: "Switch to Chat",
    routePath: paths.chat,
    icon: "chat" as IconName,
    ariaLabel: "Switch to Chat",
    dataTestId: "view-switch-btn--to-chat",
  },
} as const;

const ViewSwitchButton = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const lastSelectedChatId = useAppSelector(selectLastSelectedChatId);
  const lastSelectedAdminTab = useAppSelector(selectLastSelectedAdminTab);

  if (!keycloakService.isAdminUser()) {
    return null;
  }

  const isChatPage = location.pathname.startsWith(paths.chat);
  const isAdminPanelPage = location.pathname.startsWith(paths.adminPanel);

  if (!isChatPage && !isAdminPanelPage) {
    return null;
  }

  const currentView = isChatPage ? "chat" : "admin-panel";

  const handlePress = () => {
    if (isAdminPanelPage) {
      const chatRoute = lastSelectedChatId
        ? `${paths.chat}/${lastSelectedChatId}`
        : paths.chat;
      navigate(chatRoute, { replace: true });
    } else {
      const adminRoute = `${paths.adminPanel}/${lastSelectedAdminTab}`;
      navigate(adminRoute, { replace: true });
    }
  };

  return (
    <Tooltip
      title={options[currentView].tooltip}
      trigger={
        <IconButton
          data-testid={options[currentView].dataTestId}
          icon={options[currentView].icon}
          aria-label={options[currentView].ariaLabel}
          onPress={handlePress}
        />
      }
      placement="bottom"
    />
  );
};

export default ViewSwitchButton;
