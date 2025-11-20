// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FilesDataTable.scss";

import { DataTable, SearchBar } from "@intel-enterprise-rag-ui/components";
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
import useConditionalPolling from "@/features/admin-panel/data-ingestion/hooks/useConditionalPolling";
import { getFilesTableColumns } from "@/features/admin-panel/data-ingestion/utils/data-tables/files";

const FilesDataTable = () => {
  const { data: files, refetch, isLoading } = useGetFilesQuery();
  useConditionalPolling(files, refetch);

  const [downloadFile] = useLazyDownloadFileQuery();
  const [retryFileAction] = useRetryFileActionMutation();
  const [deleteFile] = useDeleteFileMutation();
  const [getFilePresignedUrl] = useGetFilePresignedUrlMutation();
  const [filter, setFilter] = useState("");

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

  const defaultData = files || [];

  return (
    <div className="flex flex-col gap-2">
      <SearchBar
        value={filter}
        placeholder="Filter files by status, bucket, or name"
        onChange={setFilter}
      />
      <DataTable
        defaultData={defaultData}
        columns={filesTableColumns}
        isDataLoading={isLoading}
        globalFilter={filter}
        className="files-data-table"
      />
    </div>
  );
};

export default FilesDataTable;
