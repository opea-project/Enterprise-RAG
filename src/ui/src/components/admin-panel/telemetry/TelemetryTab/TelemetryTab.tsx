// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Anchor from "@/components/shared/Anchor/Anchor";

const GRAFANA_DASHBOARD_URL = import.meta.env.VITE_GRAFANA_DASHBOARD_URL;

const TelemetryTab = () => (
  <div className="p-4">
    <Anchor href={GRAFANA_DASHBOARD_URL} isExternal>
      Grafana Dashboard
    </Anchor>
  </div>
);

export default TelemetryTab;
