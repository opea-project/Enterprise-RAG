// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./HistoryItemDetails.scss";

import { useMemo } from "react";

import GeneratedSummary from "@/components/GeneratedSummary/GeneratedSummary";
import { HistoryItemData } from "@/types";
import { getItemIcon } from "@/utils/render";

interface HistoryItemDetailsProps {
  itemData: HistoryItemData;
}

const HistoryItemDetails = ({ itemData }: HistoryItemDetailsProps) => {
  const icon = useMemo(() => getItemIcon(itemData), [itemData]);

  return (
    <div className="history-item-details">
      <header>
        {icon}
        <h2>{itemData.title}</h2>
        <p>{new Date(itemData.timestamp).toLocaleString()}</p>
      </header>
      <div className="history-item-details__summary">
        <GeneratedSummary summary={itemData.summary} />
      </div>
    </div>
  );
};

export default HistoryItemDetails;
