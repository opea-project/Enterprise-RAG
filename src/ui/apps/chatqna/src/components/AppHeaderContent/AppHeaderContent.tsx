// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ColorSchemeSwitch } from "@intel-enterprise-rag-ui/components";
import { AppNameText, UsernameText } from "@intel-enterprise-rag-ui/layouts";
import { useLocation } from "react-router-dom";

import { LogoutButton } from "@/components/LogoutButton/LogoutButton";
import ViewSwitchButton from "@/components/ViewSwitchButton/ViewSwitchButton";
import { paths } from "@/config/paths";
import ChatSideMenuIconButton from "@/features/chat/components/ChatSideMenuIconButton/ChatSideMenuIconButton";
import NewChatButton from "@/features/chat/components/NewChatButton/NewChatButton";
import { keycloakService } from "@/utils/auth";

export const AppHeaderLeftSideContent = () => {
  const location = useLocation();
  const isChatRoute = location.pathname.startsWith(paths.chat);

  return (
    <>
      {isChatRoute && <ChatSideMenuIconButton />}
      <AppNameText appName="Intel AI&reg; for Enterprise RAG" />
    </>
  );
};

export const AppHeaderRightSideContent = () => {
  const location = useLocation();
  const isSpecificChatRoute =
    location.pathname.startsWith(paths.chat) &&
    location.pathname !== paths.chat;

  return (
    <>
      {isSpecificChatRoute && <NewChatButton />}
      {keycloakService.isAdminUser() && <ViewSwitchButton />}
      <ColorSchemeSwitch />
      <UsernameText username={keycloakService.getUsername()} />
      <LogoutButton />
    </>
  );
};
