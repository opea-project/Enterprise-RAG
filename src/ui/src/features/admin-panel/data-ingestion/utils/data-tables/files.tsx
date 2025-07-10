// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ColumnDef } from "@tanstack/react-table";

import Button from "@/components/ui/Button/Button";
import ChunksProgressBar from "@/features/admin-panel/data-ingestion/components/ChunksProgressBar/ChunksProgressBar";
import DataItemStatus from "@/features/admin-panel/data-ingestion/components/DataItemStatus/DataItemStatus";
import FileTextExtractionDialog from "@/features/admin-panel/data-ingestion/components/debug/FileTextExtractionDialog/FileTextExtractionDialog";
import ProcessingTimePopup from "@/features/admin-panel/data-ingestion/components/ProcessingTimePopup/ProcessingTimePopup";
import { FileDataItem } from "@/features/admin-panel/data-ingestion/types";
import { formatFileSize } from "@/features/admin-panel/data-ingestion/utils";

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
      <ProcessingTimePopup
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
