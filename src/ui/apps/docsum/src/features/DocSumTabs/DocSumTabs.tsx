// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { TabId, Tabs } from "@intel-enterprise-rag-ui/components";
import { useCallback, useState } from "react";

import HistoryTab from "@/features/tabs/history/HistoryTab/HistoryTab";
import PasteTextTab from "@/features/tabs/paste-text/PasteTextTab/PasteTextTab";
import UploadFileTab from "@/features/tabs/upload-file/UploadFileTab/UploadFileTab";

const docsumTabs = [
  { name: "Paste Text", id: "paste-text", panel: <PasteTextTab /> },
  { name: "Upload File", id: "upload-file", panel: <UploadFileTab /> },
  {
    name: "History",
    id: "history",
    panel: <HistoryTab />,
  },
];

const DocSumTabs = () => {
  const [selectedTab, setSelectedTab] = useState<TabId>(docsumTabs[0].id);

  const handleTabSelectionChange = useCallback((id: TabId) => {
    setSelectedTab(id);
  }, []);

  return (
    <Tabs
      tabs={docsumTabs}
      selectedTab={selectedTab}
      onSelectionChange={handleTabSelectionChange}
    />
  );
};

export default DocSumTabs;
