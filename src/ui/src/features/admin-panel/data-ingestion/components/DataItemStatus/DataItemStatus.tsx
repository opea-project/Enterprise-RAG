// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataItemStatus.scss";

import classNames from "classnames";
import { ReactNode } from "react";

import BlockedIcon from "@/components/icons/BlockedIcon/BlockedIcon";
import DataPrepIcon from "@/components/icons/DataPrepIcon/DataPrepIcon";
import DeleteIcon from "@/components/icons/DeleteIcon/DeleteIcon";
import DPGuardIcon from "@/components/icons/DPGuardIcon/DPGuardIcon";
import EmbeddingIcon from "@/components/icons/EmbeddingIcon/EmbeddingIcon";
import ErrorIcon from "@/components/icons/ErrorIcon/ErrorIcon";
import LoadingIcon from "@/components/icons/LoadingIcon/LoadingIcon";
import SuccessIcon from "@/components/icons/SuccessIcon/SuccessIcon";
import UploadIcon from "@/components/icons/UploadIcon/UploadIcon";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { DataStatus } from "@/features/admin-panel/data-ingestion/types";
import { titleCaseString } from "@/utils";

const statusIconMap: Record<DataStatus, ReactNode> = {
  uploaded: <UploadIcon className="data-item-status__icon" />,
  error: <ErrorIcon className="data-item-status__icon" />,
  processing: <LoadingIcon className="data-item-status__icon" />,
  dataprep: <DataPrepIcon className="data-item-status__icon" />,
  dpguard: <DPGuardIcon className="data-item-status__icon" />,
  embedding: <EmbeddingIcon className="data-item-status__icon" />,
  ingested: <SuccessIcon className="data-item-status__icon" />,
  deleting: <DeleteIcon className="data-item-status__icon" />,
  blocked: <BlockedIcon className="data-item-status__icon" />,
};

interface DataItemStatusProps {
  status: DataStatus;
  statusMessage: string;
}

const DataItemStatus = ({ status, statusMessage }: DataItemStatusProps) => {
  const statusIcon = statusIconMap[status];
  const statusText = titleCaseString(status);
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

  const tooltipPosition = status === "error" ? "bottom right" : "right";

  return (
    <Tooltip
      title={statusMessage}
      trigger={itemStatusIndicator}
      placement={tooltipPosition}
    />
  );
};

export default DataItemStatus;
