// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AdminPanelRoute.scss";

import classNames from "classnames";
import { useCallback, useState } from "react";

import Notifications from "@/components/ui/Notifications/Notifications";
import ControlPlaneTab from "@/features/admin-panel/control-plane/components/ControlPlaneTab/ControlPlaneTab";
import DataIngestionTab from "@/features/admin-panel/data-ingestion/components/DataIngestionTab/DataIngestionTab";
import TelemetryAuthenticationTab from "@/features/admin-panel/telemetry-authentication/components/TelemetryAuthenticationTab/TelemetryAuthenticationTab";

const adminPanelTabs = [
  "Control Plane",
  "Data Ingestion",
  "Telemetry & Authentication",
];

const AdminPanelRoute = () => {
  const [selectedTabIndex, setSelectedTabIndex] = useState(0);

  const handleTabBtnClick = (selectedTabIndex: number) => {
    setSelectedTabIndex(selectedTabIndex);
  };

  const isTabSelected = useCallback(
    (tabName: string) =>
      selectedTabIndex === adminPanelTabs.findIndex((tab) => tab === tabName),
    [selectedTabIndex],
  );

  return (
    <div className="admin-panel">
      <nav className="admin-panel-tabs">
        {adminPanelTabs.map((tabName, tabIndex) => (
          <button
            key={`tab-button-${tabName}`}
            className={classNames({
              "admin-panel-tab-button": true,
              "active-tab": isTabSelected(tabName),
            })}
            onClick={() => handleTabBtnClick(tabIndex)}
          >
            {tabName}
          </button>
        ))}
      </nav>
      <div
        className={classNames({
          "admin-panel-tab-content": true,
          "data-ingestion-tab-content": isTabSelected("Data Ingestion"),
        })}
      >
        {isTabSelected("Control Plane") && <ControlPlaneTab />}
        {isTabSelected("Data Ingestion") && <DataIngestionTab />}
        {isTabSelected("Telemetry & Authentication") && (
          <TelemetryAuthenticationTab />
        )}
      </div>
      <Notifications />
    </div>
  );
};

export default AdminPanelRoute;
