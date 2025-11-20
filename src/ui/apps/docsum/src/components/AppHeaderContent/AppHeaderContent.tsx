// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LogoutButton } from "@intel-enterprise-rag-ui/auth";
import { ColorSchemeSwitch } from "@intel-enterprise-rag-ui/components";
import { AppNameText, UsernameText } from "@intel-enterprise-rag-ui/layouts";

import ViewSwitchButton from "@/components/ViewSwitchButton/ViewSwitchButton";
import { resetStore } from "@/store/utils";
import { keycloakService } from "@/utils/auth";

export const AppHeaderLeftSideContent = () => {
  return <AppNameText appName="Document Summarization" />;
};

export const AppHeaderRightSideContent = () => {
  return (
    <>
      {keycloakService.isAdminUser() && <ViewSwitchButton />}
      <ColorSchemeSwitch />
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
