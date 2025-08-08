// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FilesSyncActionCell.scss";

import classNames from "classnames";
import { ReactNode } from "react";

import DeleteIcon from "@/components/icons/DeleteIcon/DeleteIcon";
import PlusIcon from "@/components/icons/PlusIcon/PlusIcon";
import UploadIcon from "@/components/icons/UploadIcon/UploadIcon";
import { FileSyncAction } from "@/features/admin-panel/data-ingestion/types/api";
import { titleCaseString } from "@/utils";

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
