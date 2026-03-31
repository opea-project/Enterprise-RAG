// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ColumnDef } from "@tanstack/react-table";

import FilesSyncActionCell from "@/features/admin-panel/data-ingestion/components/FilesSyncActionCell/FilesSyncActionCell";
import {
  SharePointSiteItem,
  SharePointSyncDataItem,
} from "@/features/admin-panel/data-ingestion/types/api";

export const sharePointSitesColumns: ColumnDef<SharePointSiteItem>[] = [
  {
    accessorKey: "display_name",
    header: "Display Name",
    cell: ({ row }) => row.original.display_name ?? row.original.name,
  },
  {
    accessorKey: "name",
    header: "Name",
  },
  {
    accessorKey: "web_url",
    header: "URL",
    cell: ({ row }) =>
      row.original.web_url ? (
        <a
          href={row.original.web_url}
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          {row.original.web_url}
        </a>
      ) : (
        "—"
      ),
  },
];

export const sharePointSyncColumns: ColumnDef<SharePointSyncDataItem>[] = [
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
    accessorKey: "site_name",
    header: "Site",
  },
  {
    accessorKey: "object_name",
    header: "File",
    cell: ({
      row: {
        original: { object_name },
      },
    }) => (
      <div className="text-wrap" style={{ overflowWrap: "anywhere" }}>
        {object_name}
      </div>
    ),
  },
];
