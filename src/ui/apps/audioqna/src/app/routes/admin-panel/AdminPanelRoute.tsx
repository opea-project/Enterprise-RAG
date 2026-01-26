// Copyright (C) 2024-2026 Intel Corporation
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
import DataIngestionTab from "@/features/admin-panel/data-ingestion/components/DataIngestionTab/DataIngestionTab";
import TelemetryAuthenticationTab from "@/features/admin-panel/telemetry-authentication/components/TelemetryAuthenticationTab/TelemetryAuthenticationTab";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import {
  selectLastSelectedAdminTab,
  setLastSelectedAdminTab,
} from "@/store/viewNavigation.slice";

const adminPanelTabs = [
  {
    name: "Control Plane",
    path: "control-plane",
    id: "control-plane",
    panel: <ControlPlaneTab />,
  },
  {
    name: "Data Ingestion",
    path: "data-ingestion",
    id: "data-ingestion",
    panel: <DataIngestionTab />,
  },
  {
    name: "Telemetry & Authentication",
    path: "telemetry-authentication",
    id: "telemetry-authentication",
    panel: <TelemetryAuthenticationTab />,
  },
];

const AdminPanelRoute = () => {
  const dispatch = useAppDispatch();
  const lastSelectedAdminTab = useAppSelector(selectLastSelectedAdminTab);

  // Initialize selected tab from store to prevent blinking on navigation
  const [selectedTab, setSelectedTab] = useState<TabId>(() => {
    const path = window.location.pathname.split("/").pop();
    const tab = adminPanelTabs.find((tab) => tab.path === path);
    return (
      (tab?.id as TabId) ||
      (lastSelectedAdminTab as TabId) ||
      adminPanelTabs[0].path
    );
  });

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname.split("/").pop();
    const tab = adminPanelTabs.find((tab) => tab.path === path);
    if (tab !== undefined) {
      setSelectedTab(tab.id as TabId);
      // Update last selected admin tab in store
      dispatch(setLastSelectedAdminTab(tab.path));
    } else {
      // Navigate to last selected tab or default tab
      const defaultTab = lastSelectedAdminTab || adminPanelTabs[0].path;
      navigate(`/admin-panel/${defaultTab}`, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname, navigate, lastSelectedAdminTab]);

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
