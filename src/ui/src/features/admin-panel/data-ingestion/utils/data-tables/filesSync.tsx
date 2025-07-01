// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ColumnDef } from "@tanstack/react-table";

import FilesSyncActionCell from "@/features/admin-panel/data-ingestion/components/FilesSyncActionCell/FilesSyncActionCell";
import { FileSyncDataItem } from "@/features/admin-panel/data-ingestion/types/api";

export const filesSyncColumns: ColumnDef<FileSyncDataItem>[] = [
  {
    accessorKey: "action",
    header: "Action",
    cell: ({
      row: {
        original: { action },
      },
    }) => <FilesSyncActionCell action={action} />,
  },
  {
    accessorKey: "bucket_name",
    header: "Bucket",
  },
  {
    accessorKey: "object_name",
    header: "Name",
    cell: ({
      row: {
        original: { object_name: fileName },
      },
    }) => (
      <div className="text-wrap" style={{ overflowWrap: "anywhere" }}>
        {fileName}
      </div>
    ),
  },
];
