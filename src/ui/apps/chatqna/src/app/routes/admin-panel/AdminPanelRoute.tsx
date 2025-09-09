// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AdminPanelRoute.scss";

import { PageLayout } from "@intel-enterprise-rag-ui/layouts";
import classNames from "classnames";
import { useEffect, useState } from "react";
import {
  Key as AriaKey,
  Tab as AriaTab,
  TabList as AriaTabList,
  TabPanel as AriaTabPanel,
  Tabs as AriaTabs,
} from "react-aria-components";
import { useLocation, useNavigate } from "react-router-dom";

import {
  AppHeaderLeftSideContent,
  AppHeaderRightSideContent,
} from "@/components/AppHeaderContent/AppHeaderContent";
import ControlPlaneTab from "@/features/admin-panel/control-plane/components/ControlPlaneTab/ControlPlaneTab";
import DataIngestionTab from "@/features/admin-panel/data-ingestion/components/DataIngestionTab/DataIngestionTab";
import TelemetryAuthenticationTab from "@/features/admin-panel/telemetry-authentication/components/TelemetryAuthenticationTab/TelemetryAuthenticationTab";

const adminPanelTabs = [
  { name: "Control Plane", path: "control-plane", panel: <ControlPlaneTab /> },
  {
    name: "Data Ingestion",
    path: "data-ingestion",
    panel: <DataIngestionTab />,
  },
  {
    name: "Telemetry & Authentication",
    path: "telemetry-authentication",
    panel: <TelemetryAuthenticationTab />,
  },
];

const AdminPanelRoute = () => {
  const [selectedTab, setSelectedTab] = useState<AriaKey>(
    adminPanelTabs[0].path,
  );
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname.split("/").pop();
    const tab = adminPanelTabs.find((tab) => tab.path === path);
    if (tab !== undefined) {
      setSelectedTab(tab.path as AriaKey);
    } else {
      navigate(`/admin-panel/${adminPanelTabs[0].path}`, { replace: true });
    }
  }, [location.pathname, navigate]);

  const handleTabBtnClick = (path: AriaKey | null) => {
    if (path === null) {
      return;
    }
    setSelectedTab(path);
    const queryParams = location.search;
    let to = `/admin-panel/${path}`;
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
      <div className="admin-panel">
        <AriaTabs
          selectedKey={selectedTab}
          onSelectionChange={handleTabBtnClick}
        >
          <AriaTabList
            className="admin-panel-tabs"
            aria-label="Admin Panel views"
          >
            {adminPanelTabs.map((tab) => (
              <AriaTab
                key={`${tab.path}-tab`}
                id={tab.path}
                className={({ isSelected }) =>
                  classNames("admin-panel-tab-button", {
                    "active-tab": isSelected,
                  })
                }
              >
                {tab.name}
              </AriaTab>
            ))}
          </AriaTabList>
          {adminPanelTabs.map((tab) => (
            <AriaTabPanel
              key={`${tab.path}-panel`}
              id={tab.path}
              className="admin-panel-tab-content"
            >
              {tab.panel}
            </AriaTabPanel>
          ))}
        </AriaTabs>
      </div>
    </PageLayout>
  );
};

export default AdminPanelRoute;
