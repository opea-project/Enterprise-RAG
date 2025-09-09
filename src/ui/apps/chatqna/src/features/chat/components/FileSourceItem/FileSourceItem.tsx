// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconButton, Tooltip } from "@intel-enterprise-rag-ui/components";
import { FileIcon } from "@intel-enterprise-rag-ui/icons";

import {
  useGetFilePresignedUrlMutation,
  useLazyDownloadFileQuery,
} from "@/api";
import SourceItem from "@/features/chat/components/SourceItem/SourceItem";
import { FileSource } from "@/features/chat/types";

interface FileSourceItemProps {
  source: FileSource;
}

const FileSourceItem = ({
  source: { object_name: fileName, bucket_name: bucketName },
}: FileSourceItemProps) => {
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
    <SourceItem
      icon={<FileIcon />}
      name={fileName}
      actions={
        <Tooltip
          title="Download"
          trigger={
            <IconButton
              icon="download"
              size="sm"
              onPress={handleDownloadBtnPress}
            />
          }
        />
      }
    />
  );
};

export default FileSourceItem;
