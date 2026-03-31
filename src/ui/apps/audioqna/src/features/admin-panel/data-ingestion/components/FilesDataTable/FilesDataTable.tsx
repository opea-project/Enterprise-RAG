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
  useDeleteSharePointFileMutation,
  useGetFilesQuery,
  useGetSharePointSitesQuery,
  usePostSharePointFileUrlMutation,
  useRetryFileActionMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import { useDeleteFileMutation } from "@/features/admin-panel/data-ingestion/api/s3Api";
import BatchActionsDropdown from "@/features/admin-panel/data-ingestion/components/BatchActionsDropdown/BatchActionsDropdown";
import BatchDeleteDialog from "@/features/admin-panel/data-ingestion/components/BatchDeleteDialog/BatchDeleteDialog";
import useConditionalPolling from "@/features/admin-panel/data-ingestion/hooks/useConditionalPolling";
import { FileDataItem } from "@/features/admin-panel/data-ingestion/types";
import { getFilesTableColumns } from "@/features/admin-panel/data-ingestion/utils/data-tables/files";
import {
  S3_BUCKET_EMOJI,
  SHAREPOINT_SITE_EMOJI,
} from "@/features/admin-panel/utils";

const FilesDataTable = () => {
  const { data: files, refetch, isLoading } = useGetFilesQuery();
  useConditionalPolling(files, refetch);

  const { data: spSites } = useGetSharePointSitesQuery();
  const sourceMap = useMemo(() => {
    const map: Record<string, string> = {};
    if (spSites) {
      for (const site of spSites) {
        const displayName = site.display_name || site.name;
        map[displayName] = displayName;
      }
    }
    return map;
  }, [spSites]);

  const [downloadFile] = useLazyDownloadFileQuery();
  const [retryFileAction] = useRetryFileActionMutation();
  const [deleteFile] = useDeleteFileMutation();
  const [getFilePresignedUrl] = useGetFilePresignedUrlMutation();
  const [postSharePointFileUrl] = usePostSharePointFileUrlMutation();
  const [deleteSharePointFile] = useDeleteSharePointFileMutation();
  const [filter, setFilter] = useState("");
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const downloadHandler = useCallback(
    async (
      fileName: string,
      bucketName: string | null,
      siteName: string | null,
    ) => {
      if (siteName) {
        // For SharePoint files, get the SP URL and open in a new tab
        const { data } = await postSharePointFileUrl({
          site_name: siteName,
          object_name: fileName,
        });

        if (data?.url) {
          window.open(data.url, "_blank", "noopener,noreferrer");
        }
        return;
      }

      if (!bucketName) return;

      const { data: presignedUrl } = await getFilePresignedUrl({
        fileName,
        method: "GET",
        bucketName,
      });

      if (presignedUrl) {
        downloadFile({ presignedUrl, fileName });
      }
    },
    [downloadFile, getFilePresignedUrl, postSharePointFileUrl],
  );

  const retryHandler = useCallback(
    (uuid: string) => {
      retryFileAction(uuid);
    },
    [retryFileAction],
  );

  const deleteHandler = useCallback(
    async (
      fileName: string,
      bucketName: string | null,
      siteName: string | null,
    ) => {
      if (siteName) {
        deleteSharePointFile({ site_name: siteName, object_name: fileName });
        return;
      }

      if (!bucketName) return;

      const { data: presignedUrl } = await getFilePresignedUrl({
        fileName,
        method: "DELETE",
        bucketName,
      });

      if (presignedUrl) {
        deleteFile(presignedUrl);
      }
    },
    [deleteFile, getFilePresignedUrl, deleteSharePointFile],
  );

  const filesTableColumns = useMemo(
    () =>
      getFilesTableColumns({
        downloadHandler,
        retryHandler,
        deleteHandler,
        sourceMap,
      }),
    [deleteHandler, downloadHandler, retryHandler, sourceMap],
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
          data-testid="files-search-bar"
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
      {Object.keys(sourceMap).length > 0 && (
        <div className="text-light-text-primary dark:text-dark-text-primary flex gap-4 px-2 py-1 text-xs">
          <span>{S3_BUCKET_EMOJI} S3 Bucket</span>
          <span>{SHAREPOINT_SITE_EMOJI} SharePoint Site</span>
        </div>
      )}
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
