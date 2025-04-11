// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ColumnDef } from "@tanstack/react-table";

import Button from "@/components/ui/Button/Button";
import ChunksProgressBar from "@/features/admin-panel/data-ingestion/components/ChunksProgressBar/ChunksProgressBar";
import DataItemStatus from "@/features/admin-panel/data-ingestion/components/DataItemStatus/DataItemStatus";
import FileTextExtractionDialog from "@/features/admin-panel/data-ingestion/components/FileTextExtractionDialog/FileTextExtractionDialog";
import { FileDataItem } from "@/features/admin-panel/data-ingestion/types";
import {
  formatFileSize,
  formatProcessingTimePeriod,
} from "@/features/admin-panel/data-ingestion/utils";

interface FileActionsHandlers {
  downloadHandler: (name: string, bucketName: string) => void;
  retryHandler: (id: string) => void;
  deleteHandler: (name: string, bucketName: string) => void;
}

export const getFilesTableColumns = ({
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
    accessorKey: "bucket_name",
    header: "Bucket",
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
        original: { object_name, status, id, bucket_name },
      },
    }) => (
      <div className="flex items-center justify-center gap-2">
        <Button
          size="sm"
          onClick={() => downloadHandler(object_name, bucket_name)}
        >
          Download
        </Button>
        <FileTextExtractionDialog uuid={id} fileName={object_name} />
        {status === "error" && (
          <Button size="sm" variant="outlined" onClick={() => retryHandler(id)}>
            Retry
          </Button>
        )}
        <Button
          size="sm"
          color="error"
          onClick={() => deleteHandler(object_name, bucket_name)}
        >
          Delete
        </Button>
      </div>
    ),
  },
];
