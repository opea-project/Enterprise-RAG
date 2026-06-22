// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Tooltip } from "@intel-enterprise-rag-ui/components";
import {
  S3BucketIcon,
  SharePointSiteIcon,
} from "@intel-enterprise-rag-ui/icons";
import { formatFileSize } from "@intel-enterprise-rag-ui/utils";
import { ColumnDef } from "@tanstack/react-table";

import ChunksProgressBar from "@/features/admin-panel/data-ingestion/components/ChunksProgressBar/ChunksProgressBar";
import DataItemStatus from "@/features/admin-panel/data-ingestion/components/DataItemStatus/DataItemStatus";
import FileTextExtractionDialog from "@/features/admin-panel/data-ingestion/components/debug/FileTextExtractionDialog/FileTextExtractionDialog";
import EmbeddingModelIndicator from "@/features/admin-panel/data-ingestion/components/EmbeddingModelIndicator/EmbeddingModelIndicator";
import ProcessingTimePopover from "@/features/admin-panel/data-ingestion/components/ProcessingTimePopover/ProcessingTimePopover";
import { FileDataItem } from "@/features/admin-panel/data-ingestion/types";
import { formatStatusForFilter } from "@/features/admin-panel/data-ingestion/utils/data-tables/utils";
import { getAudioQnAAppEnv } from "@/utils";

// EMBEDDING_MODEL_MIGRATION_NEW_MODEL = current embedding model used by the system
// Files with a different model need to be re-ingested
const currentEmbeddingModel = getAudioQnAAppEnv(
  "EMBEDDING_MODEL_MIGRATION_NEW_MODEL",
);

interface FileActionsHandlers {
  downloadHandler: (
    name: string,
    bucketName: string | null,
    siteName: string | null,
  ) => void;
  retryHandler: (id: string) => void;
  deleteHandler: (
    name: string,
    bucketName: string | null,
    siteName: string | null,
  ) => void;
  sourceMap?: Record<string, string>;
}

export const getFilesTableColumns = ({
  downloadHandler,
  retryHandler,
  deleteHandler,
}: FileActionsHandlers): ColumnDef<FileDataItem>[] => {
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
      accessorKey: "bucket_name",
      header: "Source",
      cell: ({
        row: {
          original: { bucket_name, site_name },
        },
      }) => {
        if (site_name) {
          return (
            <span className="flex items-center gap-1">
              <SharePointSiteIcon aria-hidden="true" />
              {site_name}
            </span>
          );
        }
        return (
          <span className="flex items-center gap-1">
            <S3BucketIcon aria-hidden="true" />
            {bucket_name}
          </span>
        );
      },
    },
    {
      accessorKey: "object_name",
      header: "Name",
      cell: ({
        row: {
          original: { object_name: fileName, embedding_model },
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
              trigger={<span className="cursor-help">{fileName}</span>}
            />
          </div>
        );
      },
    },
    {
      accessorKey: "size",
      header: "Size",
      enableGlobalFilter: false,
      cell: ({ row }) => formatFileSize(row.getValue("size")),
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
          original: {
            object_name,
            status,
            id,
            bucket_name,
            site_name,
            embedding_model,
          },
        },
      }) => {
        const needsReingest =
          currentEmbeddingModel &&
          embedding_model !== currentEmbeddingModel &&
          status === "ingested";

        return (
          <div className="flex items-center justify-center gap-2">
            <Button
              data-testid="download-file-button"
              size="sm"
              onPress={() =>
                downloadHandler(object_name, bucket_name, site_name)
              }
            >
              {site_name ? "Open" : "Download"}
            </Button>
            <FileTextExtractionDialog uuid={id} fileName={object_name} />
            {status === "error" && (
              <Button
                data-testid="retry-file-button"
                size="sm"
                variant="outlined"
                onPress={() => retryHandler(id)}
              >
                Retry
              </Button>
            )}
            {needsReingest && (
              <Button
                data-testid="reingest-file-button"
                size="sm"
                variant="outlined"
                onPress={() => retryHandler(id)}
              >
                Reingest
              </Button>
            )}
            {(bucket_name || site_name) && (
              <Button
                data-testid="delete-file-button"
                size="sm"
                color="error"
                onPress={() =>
                  deleteHandler(object_name, bucket_name, site_name)
                }
              >
                Delete
              </Button>
            )}
          </div>
        );
      },
    },
  ];
};
