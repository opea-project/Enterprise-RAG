// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AdminPanelPage.scss";

import classNames from "classnames";
import { useCallback, useState } from "react";

import ControlPlaneTab from "@/components/admin-panel/control-plane/ControlPlaneTab/ControlPlaneTab";
import DataIngestionTab from "@/components/admin-panel/data-ingestion/DataIngestionTab/DataIngestionTab";
import TelemetryAuthenticationTab from "@/components/admin-panel/telemetry-authentication/TelemetryAuthenticationTab/TelemetryAuthenticationTab";
import NotificationsProvider from "@/components/shared/NotificationsProvider/NotificationsProvider";

const adminPanelTabs = [
  "Control Plane",
  "Data Ingestion",
  "Telemetry & Authentication",
];

const AdminPanelPage = () => {
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
      <NotificationsProvider />
    </div>
  );
};

export default AdminPanelPage;
