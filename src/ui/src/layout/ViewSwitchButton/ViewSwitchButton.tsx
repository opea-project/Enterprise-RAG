// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { BsDatabaseFillGear, BsFillChatLeftTextFill } from "react-icons/bs";
import { useLocation, useNavigate } from "react-router-dom";

import IconButton from "@/components/shared/IconButton/IconButton";
import Tooltip from "@/components/shared/Tooltip/Tooltip";

const ViewSwitchButton = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const isChatPage = location.pathname === "/chat";
  const tooltipTitle = isChatPage ? "Admin Panel" : "Chat";
  const routeToPath = isChatPage ? "/admin-panel" : "/chat";
  const icon = isChatPage ? <BsDatabaseFillGear /> : <BsFillChatLeftTextFill />;

  return (
    <Tooltip text={tooltipTitle}>
      <IconButton icon={icon} onClick={() => navigate(routeToPath)} />
    </Tooltip>
  );
};

export default ViewSwitchButton;
