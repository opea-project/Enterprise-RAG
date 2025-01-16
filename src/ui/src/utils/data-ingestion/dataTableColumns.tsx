// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ColumnDef } from "@tanstack/react-table";

import ChunksProgressBar from "@/components/admin-panel/data-ingestion/ChunksProgressBar/ChunksProgressBar";
import DataItemStatus from "@/components/admin-panel/data-ingestion/DataItemStatus/DataItemStatus";
import {
  FileDataItem,
  LinkDataItem,
} from "@/models/admin-panel/data-ingestion/dataIngestion";
import {
  formatFileSize,
  formatProcessingTimePeriod,
} from "@/utils/data-ingestion";

interface FileActionsHandlers {
  downloadHandler: (name: string) => void;
  retryHandler: (id: string) => void;
  deleteHandler: (name: string) => void;
}

interface LinkActionsHandlers {
  retryHandler: (id: string) => void;
  deleteHandler: (id: string) => void;
}

const getFilesTableColumns = ({
  downloadHandler,
  retryHandler,
  deleteHandler,
}: FileActionsHandlers): ColumnDef<FileDataItem>[] => [
  {
    accessorKey: "status",
    header: "Status",
    cell: ({
      row: {
        original: { status, job_message: statusMessage },
      },
    }) => <DataItemStatus status={status} statusMessage={statusMessage} />,
  },
  {
    accessorKey: "object_name",
    header: "Name",
  },
  {
    accessorKey: "size",
    header: "Size",
    cell: ({ row }) => formatFileSize(row.getValue("size")),
  },
  {
    id: "chunks",
    header: "Chunks",
    cell: ({
      row: {
        original: {
          chunks_processed: processedChunks,
          chunks_total: totalChunks,
        },
      },
    }) => (
      <ChunksProgressBar
        processedChunks={processedChunks}
        totalChunks={totalChunks}
      />
    ),
  },
  {
    header: "Processing Time",
    cell: ({
      row: {
        original: { processing_duration },
      },
    }) => formatProcessingTimePeriod(processing_duration),
  },
  {
    id: "actions",
    header: () => <p className="text-center">Actions</p>,
    cell: ({
      row: {
        original: { object_name, status, id },
      },
    }) => (
      <div className="flex items-center justify-center gap-2">
        <button
          className="button--small"
          onClick={() => downloadHandler(object_name)}
        >
          Download
        </button>
        {status === "error" && (
          <button
            className="button--small outlined-button--primary"
            onClick={() => retryHandler(id)}
          >
            Retry
          </button>
        )}
        <button
          className="button--small outlined-button--danger"
          onClick={() => deleteHandler(object_name)}
        >
          Delete
        </button>
      </div>
    ),
  },
];

const getLinksTableColumns = ({
  retryHandler,
  deleteHandler,
}: LinkActionsHandlers): ColumnDef<LinkDataItem>[] => [
  {
    accessorKey: "status",
    header: "Status",
    cell: ({
      row: {
        original: { status, job_message: statusMessage },
      },
    }) => <DataItemStatus status={status} statusMessage={statusMessage} />,
  },
  {
    accessorKey: "uri",
    header: "Link",
  },
  {
    id: "chunks",
    header: "Chunks",
    cell: ({
      row: {
        original: {
          chunks_processed: processedChunks,
          chunks_total: totalChunks,
        },
      },
    }) => (
      <ChunksProgressBar
        processedChunks={processedChunks}
        totalChunks={totalChunks}
      />
    ),
  },
  {
    header: "Processing Time",
    cell: ({
      row: {
        original: { processing_duration },
      },
    }) => formatProcessingTimePeriod(processing_duration),
  },
  {
    id: "actions",
    header: () => <p className="text-center">Actions</p>,
    cell: ({
      row: {
        original: { id, status },
      },
    }) => (
      <div className="flex items-center justify-center gap-2">
        {status === "error" && (
          <button
            className="button--small outlined-button--primary"
            onClick={() => retryHandler(id)}
          >
            Retry
          </button>
        )}
        <button
          className="button--small outlined-button--danger"
          onClick={() => deleteHandler(id)}
        >
          Delete
        </button>
      </div>
    ),
  },
];

export { getFilesTableColumns, getLinksTableColumns };
