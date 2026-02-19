// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FileIcon } from "@intel-enterprise-rag-ui/icons";

import { SourceDialog } from "@/components/sources/SourceDialog/SourceDialog";
import { FileSource } from "@/types";

interface FileSourceDialogProps {
  source: FileSource;
  onDownload: (fileName: string, bucketName: string) => void;
}

export const FileSourceDialog = ({
  source: { object_name: fileName, bucket_name: bucketName, citations },
  onDownload,
}: FileSourceDialogProps) => {
  const handleDownloadBtnPress = () => {
    onDownload(fileName, bucketName);
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
