// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import DataTable from "@/components/shared/DataTable/DataTable";
import DataIngestionService from "@/services/dataIngestionService";
import {
  filesDataIsLoadingSelector,
  filesDataSelector,
  getFiles,
} from "@/store/dataIngestion.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { addNotification } from "@/store/notifications.slice";
import { getFilesTableColumns } from "@/utils/data-ingestion/dataTableColumns";

const FilesDataTable = () => {
  const filesData = useAppSelector(filesDataSelector);
  const filesDataIsLoading = useAppSelector(filesDataIsLoadingSelector);
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(getFiles());
  }, []);

  const downloadFile = async (name: string) => {
    try {
      const downloadUrl = await DataIngestionService.getFilePresignedUrl(
        name,
        "GET",
      );

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

  const retryFileAction = async (uuid: string) => {
    try {
      await DataIngestionService.retryFileAction(uuid);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to retry file action";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    } finally {
      dispatch(getFiles());
    }
  };

  const deleteFile = async (name: string) => {
    try {
      await DataIngestionService.deleteFile(name);
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : `Failed to delete file: ${name}`;
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    } finally {
      dispatch(getFiles());
    }
  };

  const filesTableColumns = getFilesTableColumns({
    downloadHandler: downloadFile,
    retryHandler: retryFileAction,
    deleteHandler: deleteFile,
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
