// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Anchor from "@/components/shared/Anchor/Anchor";

const KEYCLOAK_ADMIN_PANEL_URL = import.meta.env.VITE_KEYCLOAK_ADMIN_PANEL_URL;

const AuthenticationTab = () => (
  <ul className="list-none p-4">
    <li>
      <Anchor href={KEYCLOAK_ADMIN_PANEL_URL} isExternal>
        Keycloak Admin Panel
      </Anchor>
    </li>
  </ul>
);

export default AuthenticationTab;
