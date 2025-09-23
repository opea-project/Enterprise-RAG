// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FileIcon } from "@intel-enterprise-rag-ui/icons";

import {
  useGetFilePresignedUrlMutation,
  useLazyDownloadFileQuery,
} from "@/api";
import SourceDialog from "@/features/chat/components/SourceDialog/SourceDialog";
import { FileSource } from "@/features/chat/types";

interface FileSourceDialogProps {
  source: FileSource;
}

const FileSourceDialog = ({
  source: { object_name: fileName, bucket_name: bucketName, citations },
}: FileSourceDialogProps) => {
  const [downloadFile] = useLazyDownloadFileQuery();
  const [getFilePresignedUrl] = useGetFilePresignedUrlMutation();

  const handleDownloadBtnPress = async () => {
    const { data: presignedUrl } = await getFilePresignedUrl({
      fileName,
      method: "GET",
      bucketName,
    });

    if (presignedUrl) {
      downloadFile({ presignedUrl, fileName });
    }
  };

  return (
    <SourceDialog
      name={fileName}
      triggerIcon={<FileIcon />}
      actionLabel="Download"
      citations={citations}
      onAction={handleDownloadBtnPress}
    />
  );
};

export default FileSourceDialog;
