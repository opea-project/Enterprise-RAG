// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ExternalLink from "@/components/shared/ExternalLink/ExternalLink";

const GRAFANA_DASHBOARD_URL = import.meta.env.VITE_GRAFANA_DASHBOARD_URL;

const TelemetryTab = () => (
  <div className="p-4">
    <ExternalLink text="Grafana Dashboard" href={GRAFANA_DASHBOARD_URL} />
  </div>
);

export default TelemetryTab;
