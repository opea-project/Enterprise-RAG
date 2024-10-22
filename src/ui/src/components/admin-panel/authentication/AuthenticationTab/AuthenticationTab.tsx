// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ExternalLink from "@/components/shared/ExternalLink/ExternalLink";

const APISIX_DASHBOARD_URL = import.meta.env.VITE_APISIX_DASHBOARD_URL;
const KEYCLOAK_ADMIN_PANEL_URL = import.meta.env.VITE_KEYCLOAK_ADMIN_PANEL_URL;

const AuthenticationTab = () => (
  <ul className="list-none p-4">
    <li>
      <ExternalLink text="APISIX Dashboard" href={APISIX_DASHBOARD_URL} />
    </li>
    <li>
      <ExternalLink
        text="Keycloak Admin Panel"
        href={KEYCLOAK_ADMIN_PANEL_URL}
      />
    </li>
  </ul>
);

export default AuthenticationTab;
