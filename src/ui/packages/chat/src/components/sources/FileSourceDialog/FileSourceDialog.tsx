// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FileIcon } from "@intel-enterprise-rag-ui/icons";

import { SourceDialog } from "@/components/sources/SourceDialog/SourceDialog";
import { FileSource } from "@/types";

interface FileSourceDialogProps {
  source: FileSource;
  onDownload: (
    fileName: string,
    bucketName: string | null,
    siteName: string | null,
  ) => void;
}

export const FileSourceDialog = ({
  source: {
    object_name: fileName,
    bucket_name: bucketName,
    site_name: siteName,
    citations,
  },
  onDownload,
}: FileSourceDialogProps) => {
  const handleActionBtnPress = () => {
    onDownload(fileName, bucketName, siteName);
  };

  return (
    <SourceDialog
      name={fileName}
      triggerIcon={<FileIcon />}
      actionLabel={siteName ? "Open" : "Download"}
      citations={citations}
      onAction={handleActionBtnPress}
    />
  );
};
