// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Tooltip } from "@intel-enterprise-rag-ui/components";
import { ColumnDef } from "@tanstack/react-table";

import ChunksProgressBar from "@/features/admin-panel/data-ingestion/components/ChunksProgressBar/ChunksProgressBar";
import DataItemStatus from "@/features/admin-panel/data-ingestion/components/DataItemStatus/DataItemStatus";
import LinkTextExtractionDialog from "@/features/admin-panel/data-ingestion/components/debug/LinkTextExtractionDialog/LinkTextExtractionDialog";
import EmbeddingModelIndicator from "@/features/admin-panel/data-ingestion/components/EmbeddingModelIndicator/EmbeddingModelIndicator";
import ProcessingTimePopover from "@/features/admin-panel/data-ingestion/components/ProcessingTimePopover/ProcessingTimePopover";
import { LinkDataItem } from "@/features/admin-panel/data-ingestion/types";
import { formatStatusForFilter } from "@/features/admin-panel/data-ingestion/utils/data-tables/utils";
import { getAudioQnAAppEnv } from "@/utils";

// EMBEDDING_MODEL_MIGRATION_NEW_MODEL = current embedding model used by the system
// Links with a different model need to be re-ingested
const currentEmbeddingModel = getAudioQnAAppEnv(
  "EMBEDDING_MODEL_MIGRATION_NEW_MODEL",
);

interface LinkActionsHandlers {
  retryHandler: (id: string) => void;
  deleteHandler: (id: string) => void;
}

export const getLinksTableColumns = ({
  retryHandler,
  deleteHandler,
}: LinkActionsHandlers): ColumnDef<LinkDataItem>[] => {
  return [
    {
      accessorKey: "status",
      header: "Status",
      accessorFn: (row) => formatStatusForFilter(row.status),
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
          original: { uri, embedding_model },
        },
      }) => {
        const tooltipContent = (
          <div className="text-xs">
            <p className="mb-1 font-semibold">Embedding Model</p>
            <p className="font-mono">{embedding_model || "unknown"}</p>
          </div>
        );

        return (
          <div
            className="flex items-center text-wrap"
            style={{ overflowWrap: "anywhere" }}
          >
            <EmbeddingModelIndicator itemEmbeddingModel={embedding_model} />
            <Tooltip
              title={tooltipContent}
              placement="top"
              trigger={<span className="cursor-help">{uri}</span>}
            />
          </div>
        );
      },
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
            late_chunking_duration,
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
          lateChunkingDuration={late_chunking_duration}
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
      header: () => <p className="w-full text-center">Actions</p>,
      cell: ({
        row: {
          original: { id, uri, status, embedding_model },
        },
      }) => {
        const needsReingest =
          currentEmbeddingModel &&
          embedding_model !== currentEmbeddingModel &&
          status === "ingested";

        return (
          <div className="flex items-center justify-center gap-2">
            <LinkTextExtractionDialog uuid={id} linkUri={uri} />
            {status === "error" && (
              <Button
                data-testid="retry-link-button"
                size="sm"
                variant="outlined"
                onPress={() => retryHandler(id)}
              >
                Retry
              </Button>
            )}
            {needsReingest && (
              <Button
                data-testid="reingest-link-button"
                size="sm"
                variant="outlined"
                onPress={() => retryHandler(id)}
              >
                Reingest
              </Button>
            )}
            <Button
              data-testid="delete-link-button"
              size="sm"
              color="error"
              onPress={() => deleteHandler(id)}
            >
              Delete
            </Button>
          </div>
        );
      },
    },
  ];
};
