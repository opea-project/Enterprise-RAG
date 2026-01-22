// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button } from "@intel-enterprise-rag-ui/components";
import { formatFileSize } from "@intel-enterprise-rag-ui/utils";
import { ColumnDef } from "@tanstack/react-table";

import ChunksProgressBar from "@/features/admin-panel/data-ingestion/components/ChunksProgressBar/ChunksProgressBar";
import DataItemStatus from "@/features/admin-panel/data-ingestion/components/DataItemStatus/DataItemStatus";
import FileTextExtractionDialog from "@/features/admin-panel/data-ingestion/components/debug/FileTextExtractionDialog/FileTextExtractionDialog";
import ProcessingTimePopover from "@/features/admin-panel/data-ingestion/components/ProcessingTimePopover/ProcessingTimePopover";
import { FileDataItem } from "@/features/admin-panel/data-ingestion/types";

import { formatStatusForFilter } from "./utils";

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
    accessorFn: (row) => formatStatusForFilter(row.status),
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
        original: { object_name, status, id, bucket_name },
      },
    }) => (
      <div className="flex items-center justify-center gap-2">
        <Button
          size="sm"
          onPress={() => downloadHandler(object_name, bucket_name)}
        >
          Download
        </Button>
        <FileTextExtractionDialog uuid={id} fileName={object_name} />
        {status === "error" && (
          <Button size="sm" variant="outlined" onPress={() => retryHandler(id)}>
            Retry
          </Button>
        )}
        <Button
          size="sm"
          color="error"
          onPress={() => deleteHandler(object_name, bucket_name)}
        >
          Delete
        </Button>
      </div>
    ),
  },
];
