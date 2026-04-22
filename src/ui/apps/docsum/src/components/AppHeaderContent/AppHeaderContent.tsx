// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LogoutButton } from "@intel-enterprise-rag-ui/auth";
import { ColorSchemeSwitch } from "@intel-enterprise-rag-ui/components";
import {
  AboutDialog,
  AppNameText,
  UsernameText,
} from "@intel-enterprise-rag-ui/layouts";

import ViewSwitchButton from "@/components/ViewSwitchButton/ViewSwitchButton";
import { resetStore } from "@/store/utils";
import { getDocSumAppEnv } from "@/utils";
import { keycloakService } from "@/utils/auth";

const APP_NAME = "Intel® AI for Enterprise RAG";
const APP_VERSION =
  getDocSumAppEnv("ERAG_VERSION") || import.meta.env.VITE_APP_VERSION;
const USER_GUIDE_URL =
  "https://github.com/opea-project/Enterprise-RAG/blob/main/docs/Intel_AI_for_Enterprise_RAG_DocSum_User_Guide_2.2.0.pdf";

export const AppHeaderLeftSideContent = () => {
  return <AppNameText appName="Document Summarization" />;
};

export const AppHeaderRightSideContent = () => {
  return (
    <>
      <ViewSwitchButton />
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
