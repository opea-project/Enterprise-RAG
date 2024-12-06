// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Anchor from "@/components/shared/Anchor/Anchor";

const APISIX_DASHBOARD_URL = import.meta.env.VITE_APISIX_DASHBOARD_URL;
const KEYCLOAK_ADMIN_PANEL_URL = import.meta.env.VITE_KEYCLOAK_ADMIN_PANEL_URL;

const AuthenticationTab = () => (
  <ul className="list-none p-4">
    <li>
      <Anchor href={APISIX_DASHBOARD_URL} isExternal>
        APISIX Dashboard
      </Anchor>
    </li>
    <li>
      <Anchor href={KEYCLOAK_ADMIN_PANEL_URL} isExternal>
        Keycloak Admin Panel
      </Anchor>
    </li>
  </ul>
);

export default AuthenticationTab;
