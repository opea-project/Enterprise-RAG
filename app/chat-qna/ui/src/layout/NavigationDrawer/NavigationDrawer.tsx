// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NavigationDrawer.scss";

import AdminPanelSettings from "@mui/icons-material/AdminPanelSettings";
import ChatBubbleIcon from "@mui/icons-material/ChatBubble";
import { Drawer, Toolbar } from "@mui/material";

import NavigationItem from "@/layout/NavigationItem/NavigationItem";
import keycloakService from "@/services/keycloakService";

const NavigationDrawer = () => {
  const isAdmin = keycloakService.isAdmin();

  return (
    <Drawer className="navigation-drawer">
      <Toolbar />
      <NavigationItem path="/chat" icon={<ChatBubbleIcon />} />
      {isAdmin && (
        <NavigationItem path="/admin-panel" icon={<AdminPanelSettings />} />
      )}
    </Drawer>
  );
};

export default NavigationDrawer;
