// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AnchorCard } from "@intel-enterprise-rag-ui/components";

import { getChatQnAAppEnv } from "@/utils";

const grafanaDashboardUrl = getChatQnAAppEnv("GRAFANA_DASHBOARD_URL");
const keycloakAdminPanelUrl = getChatQnAAppEnv("KEYCLOAK_ADMIN_PANEL_URL");

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
