// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import DataTable from "@/components/ui/DataTable/DataTable";
import {
  useGetFilePresignedUrlMutation,
  useGetFilesQuery,
  useRetryFileActionMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import {
  useDeleteFileMutation,
  useLazyDownloadFileQuery,
} from "@/features/admin-panel/data-ingestion/api/s3Api";
import useConditionalPolling from "@/features/admin-panel/data-ingestion/hooks/useConditionalPolling";
import { getFilesTableColumns } from "@/features/admin-panel/data-ingestion/utils/data-tables/files";

const FilesDataTable = () => {
  const { data: files, refetch, isLoading } = useGetFilesQuery();
  useConditionalPolling(files, refetch);

  const [downloadFile] = useLazyDownloadFileQuery();
  const [retryFileAction] = useRetryFileActionMutation();
  const [deleteFile] = useDeleteFileMutation();
  const [getFilePresignedUrl] = useGetFilePresignedUrlMutation();

  const downloadHandler = async (fileName: string, bucketName: string) => {
    const { data: presignedUrl } = await getFilePresignedUrl({
      fileName,
      method: "GET",
      bucketName,
    });

    if (presignedUrl) {
      downloadFile({ presignedUrl, fileName });
    }
  };

  const retryHandler = (uuid: string) => {
    retryFileAction(uuid);
  };

  const deleteHandler = async (fileName: string, bucketName: string) => {
    const { data: presignedUrl } = await getFilePresignedUrl({
      fileName,
      method: "DELETE",
      bucketName,
    });

    if (presignedUrl) {
      deleteFile(presignedUrl);
    }
  };

  const filesTableColumns = getFilesTableColumns({
    downloadHandler,
    retryHandler,
    deleteHandler,
  });

  const defaultData = files || [];

  return (
    <DataTable
      defaultData={defaultData}
      columns={filesTableColumns}
      isDataLoading={isLoading}
    />
  );
};

export default FilesDataTable;
