// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import AnchorCard from "@/components/ui/AnchorCard/AnchorCard";

const grafanaDashboardUrl = import.meta.env.VITE_GRAFANA_DASHBOARD_URL;
const keycloakAdminPanelUrl = import.meta.env.VITE_KEYCLOAK_ADMIN_PANEL_URL;

const TelemetryAuthenticationTab = () => (
  <div className="grid grid-cols-1 gap-4 px-16 py-8 md:grid-cols-2 lg:grid-cols-3">
    <AnchorCard
      icon="telemetry"
      text="Grafana Dashboard"
      href={grafanaDashboardUrl}
      isExternal
    />
    <AnchorCard
      icon="identity-provider"
      text="Keycloak Admin Panel"
      href={keycloakAdminPanelUrl}
      isExternal
    />
  </div>
);

export default TelemetryAuthenticationTab;
