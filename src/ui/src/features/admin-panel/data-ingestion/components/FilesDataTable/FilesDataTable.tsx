// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import DataTable from "@/components/ui/DataTable/DataTable";
import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { deleteFile } from "@/features/admin-panel/data-ingestion/api/deleteFile";
import { getFilePresignedUrl } from "@/features/admin-panel/data-ingestion/api/getFilePresignedUrl";
import { retryFileAction } from "@/features/admin-panel/data-ingestion/api/retryFileAction";
import {
  fetchFiles,
  filesDataIsLoadingSelector,
  filesDataSelector,
} from "@/features/admin-panel/data-ingestion/store/dataIngestion.slice";
import { getFilesTableColumns } from "@/features/admin-panel/data-ingestion/utils/data-tables/files";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const FilesDataTable = () => {
  const filesData = useAppSelector(filesDataSelector);
  const filesDataIsLoading = useAppSelector(filesDataIsLoadingSelector);
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(fetchFiles());
  }, []);

  const downloadHandler = async (name: string, bucketName: string) => {
    try {
      const downloadUrl = await getFilePresignedUrl(name, "GET", bucketName);

      const response = await fetch(downloadUrl);

      if (!response.ok) {
        throw new Error(`Failed to download file: ${name}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      a.remove();
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : `Failed to download file: ${name}`;
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    }
  };

  const retryHandler = async (uuid: string) => {
    try {
      await retryFileAction(uuid);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to retry file action";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    } finally {
      dispatch(fetchFiles());
    }
  };

  const deleteHandler = async (name: string, bucketName: string) => {
    try {
      await deleteFile(name, bucketName);
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : `Failed to delete file: ${name}`;
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    } finally {
      dispatch(fetchFiles());
    }
  };

  const filesTableColumns = getFilesTableColumns({
    downloadHandler,
    retryHandler,
    deleteHandler,
  });

  return (
    <DataTable
      defaultData={filesData}
      columns={filesTableColumns}
      isDataLoading={filesDataIsLoading}
    />
  );
};

export default FilesDataTable;
