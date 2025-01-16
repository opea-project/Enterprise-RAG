// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataItemStatus.scss";

import classNames from "classnames";
import { ReactNode } from "react";
import {
  FaCheckCircle,
  FaCog,
  FaDatabase,
  FaExclamationCircle,
  FaSpinner,
  FaTrash,
  FaUpload,
} from "react-icons/fa";

import Tooltip, { TooltipPosition } from "@/components/shared/Tooltip/Tooltip";
import { DataStatus } from "@/models/admin-panel/data-ingestion/dataIngestion";

const statusIconMap: Record<DataStatus, ReactNode> = {
  uploaded: <FaUpload className="data-item-status__icon" />,
  error: <FaExclamationCircle className="data-item-status__icon" />,
  processing: <FaSpinner className="data-item-status__icon animate-spin" />,
  dataprep: <FaCog className="data-item-status__icon" />,
  embedding: <FaDatabase className="data-item-status__icon" />,
  ingested: <FaCheckCircle className="data-item-status__icon" />,
  deleting: <FaTrash className="data-item-status__icon" />,
};

interface DataItemStatusProps {
  status: DataStatus;
  statusMessage: string;
}

const DataItemStatus = ({ status, statusMessage }: DataItemStatusProps) => {
  const statusIcon = statusIconMap[status];
  const statusText = status.slice(0, 1).toUpperCase() + status.slice(1);
  const isStatusMessageEmpty = statusMessage === "";
  const statusClassNames = classNames({
    "data-item-status": true,
    [`data-item-status--${status}`]: true,
    "data-item-status--with-tooltip": !isStatusMessageEmpty,
  });

  const itemStatusIndicator = (
    <div className={statusClassNames}>
      {statusIcon}
      <p className="data-item-status__text">{statusText}</p>
    </div>
  );

  if (isStatusMessageEmpty) {
    return itemStatusIndicator;
  }

  const tooltipPosition: TooltipPosition =
    status === "error" ? "bottom-right" : "right";

  return (
    <Tooltip text={statusMessage} position={tooltipPosition}>
      {itemStatusIndicator}
    </Tooltip>
  );
};

export default DataItemStatus;
