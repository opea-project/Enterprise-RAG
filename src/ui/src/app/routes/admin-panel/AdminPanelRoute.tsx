// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AdminPanelRoute.scss";

import classNames from "classnames";
import { useEffect, useState } from "react";
import { Key, Tab, TabList, TabPanel, Tabs } from "react-aria-components";
import { useLocation, useNavigate } from "react-router-dom";

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
  const [selectedTab, setSelectedTab] = useState<Key>(adminPanelTabs[0].path);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname.split("/").pop();
    const tab = adminPanelTabs.find((tab) => tab.path === path);
    if (tab !== undefined) {
      setSelectedTab(tab.path as Key);
    } else {
      navigate(`/admin-panel/${adminPanelTabs[0].path}`, { replace: true });
    }
  }, [location.pathname, navigate]);

  const handleTabBtnClick = (path: Key | null) => {
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
    <div className="admin-panel">
      <Tabs selectedKey={selectedTab} onSelectionChange={handleTabBtnClick}>
        <TabList className="admin-panel-tabs" aria-label="Admin Panel views">
          {adminPanelTabs.map((tab) => (
            <Tab
              key={`${tab.path}-tab`}
              id={tab.path}
              className={({ isSelected }) =>
                classNames("admin-panel-tab-button", {
                  "active-tab": isSelected,
                })
              }
            >
              {tab.name}
            </Tab>
          ))}
        </TabList>
        {adminPanelTabs.map((tab) => (
          <TabPanel
            key={`${tab.path}-panel`}
            id={tab.path}
            className="admin-panel-tab-content"
          >
            {tab.panel}
          </TabPanel>
        ))}
      </Tabs>
    </div>
  );
};

export default AdminPanelRoute;
