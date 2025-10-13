// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button } from "@intel-enterprise-rag-ui/components";
import { ColumnDef } from "@tanstack/react-table";

import ChunksProgressBar from "@/features/admin-panel/data-ingestion/components/ChunksProgressBar/ChunksProgressBar";
import DataItemStatus from "@/features/admin-panel/data-ingestion/components/DataItemStatus/DataItemStatus";
import LinkTextExtractionDialog from "@/features/admin-panel/data-ingestion/components/debug/LinkTextExtractionDialog/LinkTextExtractionDialog";
import ProcessingTimePopover from "@/features/admin-panel/data-ingestion/components/ProcessingTimePopover/ProcessingTimePopover";
import { LinkDataItem } from "@/features/admin-panel/data-ingestion/types";

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
    enableGlobalFilter: false,
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
    enableGlobalFilter: false,
    cell: ({
      row: {
        original: {
          text_extractor_duration,
          text_compression_duration,
          text_splitter_duration,
          dpguard_duration,
          embedding_duration,
          ingestion_duration,
          processing_duration,
          job_start_time,
          status,
        },
      },
    }) => (
      <ProcessingTimePopover
        textExtractorDuration={text_extractor_duration}
        textCompressionDuration={text_compression_duration}
        textSplitterDuration={text_splitter_duration}
        dpguardDuration={dpguard_duration}
        embeddingDuration={embedding_duration}
        ingestionDuration={ingestion_duration}
        processingDuration={processing_duration}
        jobStartTime={job_start_time}
        dataStatus={status}
      />
    ),
  },
  {
    id: "actions",
    header: () => <p className="text-center">Actions</p>,
    cell: ({
      row: {
        original: { id, uri, status },
      },
    }) => (
      <div className="flex items-center justify-center gap-2">
        <LinkTextExtractionDialog uuid={id} linkUri={uri} />
        {status === "error" && (
          <Button size="sm" variant="outlined" onPress={() => retryHandler(id)}>
            Retry
          </Button>
        )}
        <Button size="sm" color="error" onPress={() => deleteHandler(id)}>
          Delete
        </Button>
      </div>
    ),
  },
];
