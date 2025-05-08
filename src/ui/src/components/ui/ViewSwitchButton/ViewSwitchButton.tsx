// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useLocation, useNavigate } from "react-router-dom";

import { IconName } from "@/components/icons";
import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { paths } from "@/config/paths";

const ViewSwitchButton = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const isChatPage = location.pathname === paths.chat;
  const tooltipTitle = isChatPage ? "Admin Panel" : "Chat";
  const routeToPath = isChatPage ? paths.adminPanel : paths.chat;
  const icon: IconName = isChatPage ? "admin-panel" : "chat";

  return (
    <Tooltip
      title={tooltipTitle}
      trigger={<IconButton icon={icon} onClick={() => navigate(routeToPath)} />}
      placement="bottom"
    />
  );
};

export default ViewSwitchButton;
