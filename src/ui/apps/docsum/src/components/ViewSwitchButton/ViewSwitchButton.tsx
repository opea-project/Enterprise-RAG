// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconButton, Tooltip } from "@intel-enterprise-rag-ui/components";
import { IconName } from "@intel-enterprise-rag-ui/icons";
import { useLocation, useNavigate } from "react-router-dom";

import { paths } from "@/config/paths";
import { keycloakService } from "@/utils/auth";

const options = {
  docsum: {
    tooltip: "Switch to Admin Panel",
    routePath: paths.adminPanel,
    icon: "admin-panel" as IconName,
    ariaLabel: "Switch to Admin Panel",
  },
  "admin-panel": {
    tooltip: "Switch to Document Summarization",
    routePath: paths.docsum,
    icon: "plain-text" as IconName,
    ariaLabel: "Switch to Document Summarization",
  },
} as const;

const ViewSwitchButton = () => {
  const navigate = useNavigate();
  const location = useLocation();

  if (!keycloakService.isAdminUser()) {
    return null;
  }

  const isDocSumPage = location.pathname.startsWith(paths.docsum);
  const isAdminPanelPage = location.pathname.startsWith(paths.adminPanel);

  if (!isDocSumPage && !isAdminPanelPage) {
    return null;
  }

  const currentView = isDocSumPage ? "docsum" : "admin-panel";

  const handlePress = () => {
    if (isAdminPanelPage) {
      navigate(paths.docsum);
    } else {
      navigate(paths.adminPanel);
    }
  };

  return (
    <Tooltip
      title={options[currentView].tooltip}
      trigger={
        <IconButton
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
