// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LogoutButton } from "@intel-enterprise-rag-ui/auth";
import { ColorSchemeSwitch } from "@intel-enterprise-rag-ui/components";
import {
  AppNameText,
  PageLayout,
  UsernameText,
} from "@intel-enterprise-rag-ui/layouts";

import DocSumTabs from "@/features/DocSumTabs/DocSumTabs";
import { keycloakService } from "@/utils/auth";

const MainPage = () => (
  <PageLayout
    appHeaderProps={{
      leftSideContent: <AppNameText appName="Document Summarization" />,
      rightSideContent: (
        <>
          <ColorSchemeSwitch />
          <UsernameText username={keycloakService.getUsername()} />
          <LogoutButton onPress={() => keycloakService.redirectToLogout()} />
        </>
      ),
    }}
  >
    <DocSumTabs />
  </PageLayout>
);

export default MainPage;
