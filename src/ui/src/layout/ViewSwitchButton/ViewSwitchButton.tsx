// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useLocation, useNavigate } from "react-router-dom";

import IconButton from "@/components/shared/IconButton/IconButton";
import Tooltip from "@/components/shared/Tooltip/Tooltip";

const ViewSwitchButton = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const isChatPage = location.pathname === "/chat";
  const tooltipTitle = isChatPage ? "Admin Panel" : "Chat";
  const routeToPath = isChatPage ? "/admin-panel" : "/chat";
  const icon = isChatPage ? "bi:database-fill-gear" : "bi:chat-left-text-fill";

  return (
    <Tooltip text={tooltipTitle}>
      <IconButton icon={icon} onClick={() => navigate(routeToPath)} />
    </Tooltip>
  );
};

export default ViewSwitchButton;
