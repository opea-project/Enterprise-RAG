// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Tabs.scss";

import classNames from "classnames";
import {
  Key as AriaKey,
  Tab as AriaTab,
  TabList as AriaTabList,
  TabPanel as AriaTabPanel,
  Tabs as AriaTabs,
  TabsProps as AriaTabsProps,
} from "react-aria-components";

export type TabId = AriaKey;

export interface Tab {
  name: string;
  id: TabId;
  panel: React.ReactNode;
  [key: string]: unknown;
}

interface TabsProps extends AriaTabsProps {
  /* Array that defines tab elements */
  tabs: Tab[];
  /* Currently selected tab */
  selectedTab: TabId;
  /* Handler for tab selection changes */
  onSelectionChange: (key: TabId) => void;
}

export const Tabs = ({
  tabs,
  selectedTab,
  onSelectionChange,
  ...rest
}: TabsProps) => (
  <AriaTabs
    selectedKey={selectedTab}
    onSelectionChange={onSelectionChange}
    {...rest}
  >
    <AriaTabList className="tabs">
      {tabs.map((tab) => (
        <AriaTab
          key={`${tab.id}-tab`}
          id={tab.id}
          className={({ isSelected }) =>
            classNames("tab-button", {
              "active-tab": isSelected,
            })
          }
          aria-label={`${tab.name} Tab`}
        >
          {tab.name}
        </AriaTab>
      ))}
    </AriaTabList>
    {tabs.map((tab) => (
      <AriaTabPanel key={`${tab.id}-panel`} id={tab.id} className="tab-panel">
        {tab.panel}
      </AriaTabPanel>
    ))}
  </AriaTabs>
);
