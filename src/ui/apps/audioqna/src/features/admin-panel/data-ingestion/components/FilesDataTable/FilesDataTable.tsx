// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FilesDataTable.scss";

import {
  DataTable,
  RowSelectionState,
  SearchBar,
} from "@intel-enterprise-rag-ui/components";
import { useCallback, useMemo, useState } from "react";

import {
  useGetFilePresignedUrlMutation,
  useLazyDownloadFileQuery,
} from "@/api";
import {
  useGetFilesQuery,
  useRetryFileActionMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import { useDeleteFileMutation } from "@/features/admin-panel/data-ingestion/api/s3Api";
import BatchActionsDropdown from "@/features/admin-panel/data-ingestion/components/BatchActionsDropdown/BatchActionsDropdown";
import BatchDeleteDialog from "@/features/admin-panel/data-ingestion/components/BatchDeleteDialog/BatchDeleteDialog";
import useConditionalPolling from "@/features/admin-panel/data-ingestion/hooks/useConditionalPolling";
import { FileDataItem } from "@/features/admin-panel/data-ingestion/types";
import { getFilesTableColumns } from "@/features/admin-panel/data-ingestion/utils/data-tables/files";

const FilesDataTable = () => {
  const { data: files, refetch, isLoading } = useGetFilesQuery();
  useConditionalPolling(files, refetch);

  const [downloadFile] = useLazyDownloadFileQuery();
  const [retryFileAction] = useRetryFileActionMutation();
  const [deleteFile] = useDeleteFileMutation();
  const [getFilePresignedUrl] = useGetFilePresignedUrlMutation();
  const [filter, setFilter] = useState("");
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const downloadHandler = useCallback(
    async (fileName: string, bucketName: string) => {
      const { data: presignedUrl } = await getFilePresignedUrl({
        fileName,
        method: "GET",
        bucketName,
      });

      if (presignedUrl) {
        downloadFile({ presignedUrl, fileName });
      }
    },
    [downloadFile, getFilePresignedUrl],
  );

  const retryHandler = useCallback(
    (uuid: string) => {
      retryFileAction(uuid);
    },
    [retryFileAction],
  );

  const deleteHandler = useCallback(
    async (fileName: string, bucketName: string) => {
      const { data: presignedUrl } = await getFilePresignedUrl({
        fileName,
        method: "DELETE",
        bucketName,
      });

      if (presignedUrl) {
        deleteFile(presignedUrl);
      }
    },
    [deleteFile, getFilePresignedUrl],
  );

  const filesTableColumns = useMemo(
    () =>
      getFilesTableColumns({
        downloadHandler,
        retryHandler,
        deleteHandler,
      }),
    [deleteHandler, downloadHandler, retryHandler],
  );

  const defaultData = useMemo(() => files ?? [], [files]);

  const selectedFiles = useMemo(() => {
    return Object.keys(rowSelection)
      .map((id) => defaultData.find((file) => file.id === id))
      .filter((file): file is FileDataItem => file !== undefined);
  }, [rowSelection, defaultData]);

  const retryableFiles = useMemo(() => {
    return selectedFiles.filter((file) => file.status === "error");
  }, [selectedFiles]);

  const handleBatchRetry = useCallback(async () => {
    await Promise.all(retryableFiles.map((file) => retryFileAction(file.id)));
    setRowSelection({});
  }, [retryableFiles, retryFileAction]);

  const handleBatchDelete = useCallback(async () => {
    await Promise.all(
      selectedFiles.map((file) =>
        deleteHandler(file.object_name, file.bucket_name),
      ),
    );
    setRowSelection({});
  }, [selectedFiles, deleteHandler]);

  const selectedFileNames = useMemo(() => {
    return selectedFiles.map((file) => file.object_name);
  }, [selectedFiles]);

  const getRowId = useCallback((row: FileDataItem) => row.id, []);

  return (
    <div className="files-data-table-wrapper">
      <div className="files-data-table-wrapper__header">
        <SearchBar
          value={filter}
          placeholder="Filter files by status, bucket, or name"
          onChange={setFilter}
        />
        <BatchActionsDropdown
          selectedCount={selectedFiles.length}
          retryableCount={retryableFiles.length}
          onRetry={handleBatchRetry}
          onDelete={() => setIsDeleteDialogOpen(true)}
        />
      </div>
      <DataTable
        defaultData={defaultData}
        columns={filesTableColumns}
        isDataLoading={isLoading}
        globalFilter={filter}
        className="files-data-table"
        rowSelection={rowSelection}
        onRowSelectionChange={setRowSelection}
        getRowId={getRowId}
        enableRowSelection
      />
      <BatchDeleteDialog
        isOpen={isDeleteDialogOpen}
        itemType="files"
        itemNames={selectedFileNames}
        onConfirm={handleBatchDelete}
        onClose={() => setIsDeleteDialogOpen(false)}
      />
    </div>
  );
};

export default FilesDataTable;
