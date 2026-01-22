// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { TabId, Tabs } from "@intel-enterprise-rag-ui/components";
import { PageLayout } from "@intel-enterprise-rag-ui/layouts";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import {
  AppHeaderLeftSideContent,
  AppHeaderRightSideContent,
} from "@/components/AppHeaderContent/AppHeaderContent";
import HistoryTab from "@/features/docsum/components/tabs/history/HistoryTab/HistoryTab";
import PasteTextTab from "@/features/docsum/components/tabs/paste-text/PasteTextTab/PasteTextTab";
import UploadFileTab from "@/features/docsum/components/tabs/upload-file/UploadFileTab/UploadFileTab";

const docsumTabs = [
  {
    name: "Paste Text",
    path: "paste-text",
    id: "paste-text",
    panel: <PasteTextTab />,
  },
  {
    name: "Upload File",
    path: "upload-file",
    id: "upload-file",
    panel: <UploadFileTab />,
  },
  {
    name: "History",
    path: "history",
    id: "history",
    panel: <HistoryTab />,
  },
];

const DocSumRoute = () => {
  const [selectedTab, setSelectedTab] = useState<TabId>(docsumTabs[0].path);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname.split("/").pop();
    const tab = docsumTabs.find((tab) => tab.path === path);
    if (tab !== undefined) {
      setSelectedTab(tab.id as TabId);
    } else {
      navigate(`/docsum/${docsumTabs[0].path}`, { replace: true });
    }
  }, [location.pathname, navigate]);

  const handleTabSelectionChange = (id: TabId) => {
    setSelectedTab(id);
    const tab = docsumTabs.find((tab) => tab.id === id);
    const queryParams = location.search;
    if (!tab) return;

    let to = `/docsum/${tab.path}`;
    if (queryParams) {
      to += queryParams;
    }
    navigate(to);
  };

  return (
    <PageLayout
      appHeaderProps={{
        leftSideContent: <AppHeaderLeftSideContent />,
        rightSideContent: <AppHeaderRightSideContent />,
      }}
    >
      <Tabs
        tabs={docsumTabs}
        selectedTab={selectedTab}
        onSelectionChange={handleTabSelectionChange}
      />
    </PageLayout>
  );
};

export default DocSumRoute;
