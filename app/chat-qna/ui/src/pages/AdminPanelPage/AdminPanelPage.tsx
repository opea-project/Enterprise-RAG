// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AdminPanelPage.scss";

import classNames from "classnames";
import { useCallback, useState } from "react";

import ConfigureServicesTab from "@/components/admin-panel/configure-services/ConfigureServicesTab/ConfigureServicesTab";
import DataIngestionTab from "@/components/admin-panel/data-ingestion/DataIngestionTab/DataIngestionTab";
import TelemetryTab from "@/components/admin-panel/telemetry/TelemetryTab/TelemetryTab";

const adminPanelTabs = ["Data Ingestion", "Telemetry", "Configure Services"];

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
        {isTabSelected("Data Ingestion") && <DataIngestionTab />}
        {isTabSelected("Telemetry") && <TelemetryTab />}
        {isTabSelected("Configure Services") && <ConfigureServicesTab />}
      </div>
    </div>
  );
};

export default AdminPanelPage;
