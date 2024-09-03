// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AdminPanelPage.scss";

import { Tab, Tabs } from "@mui/material";
import { SyntheticEvent, useState } from "react";

import ConfigureServicesTab from "@/components/admin-panel/configure-services/ConfigureServicesTab/ConfigureServicesTab";
import DataIngestionTab from "@/components/admin-panel/data-ingestion/DataIngestionTab/DataIngestionTab";
import TelemetryTab from "@/components/admin-panel/telemetry/TelemetryTab/TelemetryTab";

const AdminPanelPage = () => {
  const [tabIndex, setTabIndex] = useState(0);

  const handleTabChange = (_: SyntheticEvent, selectedTabIndex: number) => {
    setTabIndex(selectedTabIndex);
  };

  return (
    <div className="admin-panel">
      <Tabs
        value={tabIndex}
        onChange={handleTabChange}
        className="admin-panel-tabs"
      >
        <Tab label="Data Ingestion" />
        <Tab label="Telemetry" />
        <Tab label="Configure Services" />
      </Tabs>
      <div className="admin-panel-tab">
        {tabIndex === 0 && <DataIngestionTab />}
        {tabIndex === 1 && <TelemetryTab />}
        {tabIndex === 2 && <ConfigureServicesTab />}
      </div>
    </div>
  );
};

export default AdminPanelPage;
