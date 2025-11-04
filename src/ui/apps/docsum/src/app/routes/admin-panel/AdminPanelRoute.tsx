// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { TabId, Tabs } from "@intel-enterprise-rag-ui/components";
import { PageLayout } from "@intel-enterprise-rag-ui/layouts";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import {
  AppHeaderLeftSideContent,
  AppHeaderRightSideContent,
} from "@/components/AppHeaderContent/AppHeaderContent";
import ControlPlaneTab from "@/features/admin-panel/control-plane/components/ControlPlaneTab/ControlPlaneTab";
import TelemetryAuthenticationTab from "@/features/admin-panel/telemetry-authentication/components/TelemetryAuthenticationTab/TelemetryAuthenticationTab";

const adminPanelTabs = [
  {
    name: "Control Plane",
    path: "control-plane",
    id: "control-plane",
    panel: <ControlPlaneTab />,
  },
  {
    name: "Telemetry & Authentication",
    path: "telemetry-authentication",
    id: "telemetry-authentication",
    panel: <TelemetryAuthenticationTab />,
  },
];

const AdminPanelRoute = () => {
  const [selectedTab, setSelectedTab] = useState<TabId>(adminPanelTabs[0].path);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname.split("/").pop();
    const tab = adminPanelTabs.find((tab) => tab.path === path);
    if (tab !== undefined) {
      setSelectedTab(tab.id as TabId);
    } else {
      navigate(`/admin-panel/${adminPanelTabs[0].path}`, { replace: true });
    }
  }, [location.pathname, navigate]);

  const handleTabSelectionChange = (id: TabId) => {
    setSelectedTab(id);
    const tab = adminPanelTabs.find((tab) => tab.id === id);
    const queryParams = location.search;
    if (!tab) return;

    let to = `/admin-panel/${tab.path}`;
    if (queryParams) {
      to += queryParams;
    }
    navigate(to);
  };

  return (
    <PageLayout
      appHeaderProps={{
        leftSideContent: <AppHeaderLeftSideContent />,
        rightSideContent: <AppHeaderRightSideContent />,
      }}
    >
      <Tabs
        tabs={adminPanelTabs}
        selectedTab={selectedTab}
        onSelectionChange={handleTabSelectionChange}
      />
    </PageLayout>
  );
};

export default AdminPanelRoute;
