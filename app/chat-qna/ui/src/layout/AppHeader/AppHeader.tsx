// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AppHeader.scss";

import { AppBar, Button, Toolbar, Typography } from "@mui/material";

import keycloakService from "@/services/keycloakService";

const AppHeader = () => {
  const username = keycloakService.getUsername();

  return (
    <AppBar className="app-header">
      <Toolbar className="app-header-toolbar">
        <Typography variant="toolbar-app-name">Enterprise RAG</Typography>
        <span className="app-header-actions">
          <Typography variant="caption">{username}</Typography>
          <Button onClick={keycloakService.logout}>Logout</Button>
        </span>
      </Toolbar>
    </AppBar>
  );
};

export default AppHeader;
