// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ColumnDef } from "@tanstack/react-table";

import Button from "@/components/ui/Button/Button";
import ChunksProgressBar from "@/features/admin-panel/data-ingestion/components/ChunksProgressBar/ChunksProgressBar";
import DataItemStatus from "@/features/admin-panel/data-ingestion/components/DataItemStatus/DataItemStatus";
import { LinkDataItem } from "@/features/admin-panel/data-ingestion/types";
import { formatProcessingTimePeriod } from "@/features/admin-panel/data-ingestion/utils";

interface LinkActionsHandlers {
  retryHandler: (id: string) => void;
  deleteHandler: (id: string) => void;
}

export const getLinksTableColumns = ({
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
    cell: ({
      row: {
        original: { uri },
      },
    }) => (
      <div className="text-wrap" style={{ overflowWrap: "anywhere" }}>
        {uri}
      </div>
    ),
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
          <Button size="sm" variant="outlined" onClick={() => retryHandler(id)}>
            Retry
          </Button>
        )}
        <Button size="sm" color="error" onClick={() => deleteHandler(id)}>
          Delete
        </Button>
      </div>
    ),
  },
];
