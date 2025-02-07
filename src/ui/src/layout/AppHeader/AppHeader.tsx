// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AppHeader.scss";

import ColorSchemeSwitch from "@/layout/ColorSchemeSwitch/ColorSchemeSwitch";
import LogoutButton from "@/layout/LogoutButton/LogoutButton";
import ViewSwitchButton from "@/layout/ViewSwitchButton/ViewSwitchButton";
import keycloakService from "@/services/keycloakService";

const AppHeader = () => {
  const username = keycloakService.getUsername();
  const isAdmin = keycloakService.isAdmin();

  return (
    <header className="app-header">
      <p className="app-header__app-name">Intel AI&reg; for Enterprise RAG</p>
      <div className="app-header__actions">
        {isAdmin && <ViewSwitchButton />}
        <ColorSchemeSwitch />
        <p className="app-header__username">{username}</p>
        <LogoutButton />
      </div>
    </header>
  );
};

export default AppHeader;
