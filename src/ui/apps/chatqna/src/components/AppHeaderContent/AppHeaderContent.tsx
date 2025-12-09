// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LogoutButton } from "@intel-enterprise-rag-ui/auth";
import { ColorSchemeSwitch } from "@intel-enterprise-rag-ui/components";
import {
  AboutDialog,
  AppNameText,
  UsernameText,
} from "@intel-enterprise-rag-ui/layouts";
import { useLocation } from "react-router-dom";

import ViewSwitchButton from "@/components/ViewSwitchButton/ViewSwitchButton";
import { paths } from "@/config/paths";
import ChatSideMenuIconButton from "@/features/chat/components/ChatSideMenuIconButton/ChatSideMenuIconButton";
import NewChatButton from "@/features/chat/components/NewChatButton/NewChatButton";
import { resetStore } from "@/store/utils";
import { getChatQnAAppEnv } from "@/utils";
import { keycloakService } from "@/utils/auth";

const APP_NAME = "Intel® AI for Enterprise RAG";
const APP_VERSION =
  getChatQnAAppEnv("ERAG_VERSION") || import.meta.env.VITE_APP_VERSION;
const USER_GUIDE_URL =
  "https://github.com/opea-project/Enterprise-RAG/blob/main/docs/Intel_AI_for_Enterprise_RAG_User_Guide_2.0.0.pdf";

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
      <AboutDialog
        appName={APP_NAME}
        appVersion={APP_VERSION}
        userGuideUrl={USER_GUIDE_URL}
      />
      <UsernameText username={keycloakService.getUsername()} />
      <LogoutButton
        onPress={() => {
          resetStore();
          keycloakService.redirectToLogout();
        }}
      />
    </>
  );
};
