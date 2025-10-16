// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./HistoryTab.scss";

import { useCallback, useState } from "react";

import HistoryItem from "@/features/tabs/history/HistoryItem/HistoryItem";
import HistoryItemDetails from "@/features/tabs/history/HistoryItemDetails/HistoryItemDetails";
import { selectHistoryItems } from "@/features/tabs/history/store/history.slice";
import { useAppSelector } from "@/store/hooks";
import { HistoryItemData } from "@/types";

const HistoryTab = () => {
  const [selectedItemData, setSelectedItemData] =
    useState<HistoryItemData | null>(null);

  const items = useAppSelector(selectHistoryItems);

  const handleItemSelect = useCallback((item: HistoryItemData) => {
    setSelectedItemData(item);
  }, []);

  return (
    <div className="history-tab">
      <div className="history-list-col">
        <p>Summary History</p>
        <div className="history-list-col__items-list">
          {items.length === 0 && (
            <p className="history-list-col__items-list__no-history">
              No history items available
            </p>
          )}
          {items.length > 0 &&
            items.map((item) => (
              <HistoryItem
                key={item.id}
                itemData={item}
                isActive={selectedItemData?.id === item.id}
                onItemSelect={handleItemSelect}
              />
            ))}
        </div>
      </div>
      <div className="history-details-col">
        {selectedItemData === null && (
          <p className="history-details-col__no-selection">
            Select item from the list to view summary details
          </p>
        )}
        {selectedItemData !== null && (
          <HistoryItemDetails itemData={selectedItemData} />
        )}
      </div>
    </div>
  );
};

export default HistoryTab;
