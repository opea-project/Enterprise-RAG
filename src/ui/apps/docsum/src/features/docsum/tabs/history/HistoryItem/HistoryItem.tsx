// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./HistoryItem.scss";

import { Anchor, Tooltip } from "@intel-enterprise-rag-ui/components";
import classNames from "classnames";
import { useMemo, useState } from "react";

import HistoryItemMenu from "@/features/docsum/tabs/history/HistoryItemMenu/HistoryItemMenu";
import { HistoryItemData } from "@/types";
import { getItemIcon } from "@/utils/render";

const TITLE_OVERFLOW_LIMIT = 22;

interface HistoryItemProps {
  itemData: HistoryItemData;
  isActive: boolean;
  onItemSelect: (item: HistoryItemData) => void;
}

const HistoryItem = ({
  itemData,
  isActive,
  onItemSelect,
}: HistoryItemProps) => {
  const { title } = itemData;

  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleEntryPress = () => {
    onItemSelect(itemData);
  };

  const className = classNames("history-item", {
    "history-item--active": isActive,
    "history-item--has-menu-open": isMenuOpen,
  });

  let titleElement = <span className="history-item__title">{title}</span>;

  if (title.length > TITLE_OVERFLOW_LIMIT) {
    const truncatedTitle = `${title.slice(0, TITLE_OVERFLOW_LIMIT)}...`;
    titleElement = (
      <Tooltip
        title={title}
        trigger={<span className="history-item__title">{truncatedTitle}</span>}
        placement="right"
        className="history-item__title"
      />
    );
  }

  const icon = useMemo(() => getItemIcon(itemData), [itemData]);

  return (
    <Anchor className={className} onPress={handleEntryPress}>
      {icon}
      {titleElement}
      <HistoryItemMenu
        itemData={itemData}
        isOpen={isMenuOpen}
        onOpenChange={setIsMenuOpen}
      />
    </Anchor>
  );
};

export default HistoryItem;
