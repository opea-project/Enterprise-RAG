// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PageLayout } from "@intel-enterprise-rag-ui/layouts";

import {
  AppHeaderLeftSideContent,
  AppHeaderRightSideContent,
} from "@/components/AppHeaderContent/AppHeaderContent";
import DocSumTabs from "@/features/docsum/DocSumTabs/DocSumTabs";

const DocSumRoute = () => (
  <PageLayout
    appHeaderProps={{
      leftSideContent: <AppHeaderLeftSideContent />,
      rightSideContent: <AppHeaderRightSideContent />,
    }}
  >
    <DocSumTabs />
  </PageLayout>
);

export default DocSumRoute;
