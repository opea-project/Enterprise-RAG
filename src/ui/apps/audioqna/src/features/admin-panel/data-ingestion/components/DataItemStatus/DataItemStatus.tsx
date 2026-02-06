// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataItemStatus.scss";

import { Tooltip } from "@intel-enterprise-rag-ui/components";
import {
  BlockedIcon,
  CanceledIcon,
  DataPrepIcon,
  DeleteIcon,
  DPGuardIcon,
  EmbeddingIcon,
  ErrorIcon,
  LoadingIcon,
  SuccessIcon,
  UploadIcon,
} from "@intel-enterprise-rag-ui/icons";
import { titleCaseString } from "@intel-enterprise-rag-ui/utils";
import classNames from "classnames";
import { memo, ReactNode } from "react";

import { DataStatus } from "@/features/admin-panel/data-ingestion/types";

const statusIconMap: Record<DataStatus, ReactNode> = {
  uploaded: <UploadIcon />,
  error: <ErrorIcon />,
  processing: <LoadingIcon />,
  text_extracting: <DataPrepIcon />,
  text_compression: <DataPrepIcon />,
  text_splitting: <DataPrepIcon />,
  dpguard: <DPGuardIcon />,
  late_chunking: <EmbeddingIcon />,
  embedding: <EmbeddingIcon />,
  ingested: <SuccessIcon />,
  deleting: <DeleteIcon />,
  canceled: <CanceledIcon />,
  blocked: <BlockedIcon />,
};

const formatStatus = (status: DataStatus): string =>
  status
    .split("_")
    .map((part) => titleCaseString(part))
    .join(" ");

interface DataItemStatusProps {
  status: DataStatus;
  statusMessage: string;
}

const DataItemStatus = memo(
  ({ status, statusMessage }: DataItemStatusProps) => {
    const statusIcon = statusIconMap[status];
    const statusText = !status ? "Unknown" : formatStatus(status);
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
  },
);

DataItemStatus.displayName = "DataItemStatus";

export default DataItemStatus;
