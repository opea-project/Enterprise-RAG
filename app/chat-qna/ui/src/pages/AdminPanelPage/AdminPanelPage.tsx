// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AdminPanelPage.scss";

import classNames from "classnames";
import { useCallback, useState } from "react";

import AuthenticationTab from "@/components/admin-panel/authentication/AuthenticationTab/AuthenticationTab";
import ControlPlaneTab from "@/components/admin-panel/control-plane/ControlPlaneTab/ControlPlaneTab";
import DataIngestionTab from "@/components/admin-panel/data-ingestion/DataIngestionTab/DataIngestionTab";
import TelemetryTab from "@/components/admin-panel/telemetry/TelemetryTab/TelemetryTab";

const adminPanelTabs = [
  "Control Plane",
  "Data Ingestion",
  "Telemetry",
  "Authentication",
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
        {isTabSelected("Telemetry") && <TelemetryTab />}
        {isTabSelected("Authentication") && <AuthenticationTab />}
      </div>
    </div>
  );
};

export default AdminPanelPage;
