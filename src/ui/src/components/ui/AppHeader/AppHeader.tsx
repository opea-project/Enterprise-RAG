// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AppHeader.scss";

import { ReactNode } from "react";

import ColorSchemeSwitch from "@/components/ui/ColorSchemeSwitch/ColorSchemeSwitch";
import LogoutButton from "@/components/ui/LogoutButton/LogoutButton";
import ViewSwitchButton from "@/components/ui/ViewSwitchButton/ViewSwitchButton";
import { keycloakService } from "@/lib/auth";

export interface AppHeaderProps {
  extraActions?: ReactNode;
  leftSideMenuTrigger?: ReactNode;
}

const AppHeader = ({ extraActions, leftSideMenuTrigger }: AppHeaderProps) => (
  <header className="app-header">
    <div className="app-header__actions">
      {leftSideMenuTrigger}
      <p className="app-header__app-name">Intel AI&reg; for Enterprise RAG</p>
    </div>
    <div className="app-header__actions">
      {extraActions}
      {keycloakService.isAdminUser() && <ViewSwitchButton />}
      <ColorSchemeSwitch />
      <p className="app-header__username">{keycloakService.getUsername()}</p>
      <LogoutButton />
    </div>
  </header>
);

export default AppHeader;
