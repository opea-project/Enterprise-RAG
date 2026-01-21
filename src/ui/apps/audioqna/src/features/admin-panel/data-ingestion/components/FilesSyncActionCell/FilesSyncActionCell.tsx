// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FilesSyncActionCell.scss";

import {
  DeleteIcon,
  PlusIcon,
  UploadIcon,
} from "@intel-enterprise-rag-ui/icons";
import { titleCaseString } from "@intel-enterprise-rag-ui/utils";
import classNames from "classnames";
import { ReactNode } from "react";

import { FileSyncAction } from "@/features/admin-panel/data-ingestion/types/api";

const actionIconMap: Record<FileSyncAction, ReactNode> = {
  add: <PlusIcon />,
  "no action": null,
  delete: <DeleteIcon />,
  update: <UploadIcon />,
};

interface FilesSyncActionCellProps {
  action: FileSyncAction;
}

const FilesSyncActionCell = ({ action }: FilesSyncActionCellProps) => {
  const className = classNames("files-sync-action-cell", {
    "files-sync-action-cell--add": action === "add",
    "files-sync-action-cell--delete": action === "delete",
    "files-sync-action-cell--update": action === "update",
  });

  const icon = actionIconMap[action];

  return (
    <div className={className}>
      {icon}
      <p>{titleCaseString(action)}</p>
    </div>
  );
};

export default FilesSyncActionCell;
