// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadDataDialog.scss";

import {
  addNotification,
  Dialog,
  DialogRef,
  IconButton,
  SelectInputChangeHandler,
  Tooltip,
} from "@intel-enterprise-rag-ui/components";
import { useRef, useState } from "react";

import { useGetFilePresignedUrlMutation } from "@/api";
import {
  useLazyGetFilesQuery,
  useLazyGetLinksQuery,
  usePostLinksMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import { usePostFileMutation } from "@/features/admin-panel/data-ingestion/api/s3Api";
import BucketsDropdown from "@/features/admin-panel/data-ingestion/components/BucketsDropdown/BucketsDropdown";
import FilesIngestionPanel from "@/features/admin-panel/data-ingestion/components/FilesIngestionPanel/FilesIngestionPanel";
import LinksIngestionPanel from "@/features/admin-panel/data-ingestion/components/LinksIngestionPanel/LinksIngestionPanel";
import UploadDataDialogFooter from "@/features/admin-panel/data-ingestion/components/UploadDataDialogFooter/UploadDataDialogFooter";
import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import {
  LinkForIngestion,
  UploadErrors,
} from "@/features/admin-panel/data-ingestion/types";
import {
  createToBeUploadedMessage,
  isUploadDisabled,
} from "@/features/admin-panel/data-ingestion/utils";
import { useAppDispatch } from "@/store/hooks";
import { getErrorMessage } from "@/utils/api";

const initialUploadErrors = {
  files: "",
  links: "",
};

const UploadDataDialog = () => {
  const [getFiles] = useLazyGetFilesQuery();
  const [getLinks] = useLazyGetLinksQuery();
  const [getFilePresignedUrl] = useGetFilePresignedUrlMutation();
  const [postFile] = usePostFileMutation();
  const [postLinks] = usePostLinksMutation();

  const [files, setFiles] = useState<File[]>([]);
  const [links, setLinks] = useState<LinkForIngestion[]>([]);
  const [selectedBucket, setSelectedBucket] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadErrors, setUploadErrors] =
    useState<UploadErrors>(initialUploadErrors);

  const dialogRef = useRef<DialogRef>(null);

  const dispatch = useAppDispatch();

  const onBucketChange: SelectInputChangeHandler<string> = (value) => {
    setSelectedBucket(value);
  };

  const resetUploadErrors = () => {
    setUploadErrors(initialUploadErrors);
  };

  const onDialogClose = () => {
    setFiles([]);
    setLinks([]);
    resetUploadErrors();
    dialogRef.current?.close();
  };

  const submitUploadData = async () => {
    resetUploadErrors();
    setIsUploading(true);

    let filesUploadError = "";
    let linksUploadError = "";

    if (files.length && selectedBucket !== "") {
      let error;
      for (const file of files) {
        const { data: presignedUrl, error: getFilePresignedUrlError } =
          await getFilePresignedUrl({
            fileName: file.name,
            method: "PUT",
            bucketName: selectedBucket,
          });

        if (getFilePresignedUrlError) {
          error = getFilePresignedUrlError;
          break;
        }

        if (presignedUrl) {
          const { error: postFileError } = await postFile({
            url: presignedUrl,
            file,
          });

          if (postFileError) {
            error = postFileError;
            break;
          }
        }
      }

      if (error) {
        filesUploadError = getErrorMessage(error, ERROR_MESSAGES.POST_FILES);
      } else {
        setFiles([]);
      }
    }

    if (links.length) {
      const linksUrls = links.map(({ value }) => value);
      const { error } = await postLinks(linksUrls);

      if (error) {
        linksUploadError = getErrorMessage(error, ERROR_MESSAGES.POST_LINKS);
      } else {
        setLinks([]);
      }
    }

    if (filesUploadError || linksUploadError) {
      setUploadErrors({
        links: linksUploadError,
        files: filesUploadError,
      });
    } else {
      setUploadErrors(initialUploadErrors);
      onDialogClose();
      dispatch(
        addNotification({
          text: "Successful data upload!",
          severity: "success",
        }),
      );
      Promise.all([getFiles().refetch(), getLinks().refetch()]);
    }

    setIsUploading(false);
  };

  const toBeUploadedMessage = createToBeUploadedMessage(
    files,
    selectedBucket,
    links,
  );

  return (
    <Dialog
      ref={dialogRef}
      trigger={
        <Tooltip
          title="Upload Data"
          trigger={<IconButton icon="upload" variant="contained" />}
        />
      }
      footer={
        <UploadDataDialogFooter
          uploadErrors={uploadErrors}
          toBeUploadedMessage={toBeUploadedMessage}
          isUploadDisabled={isUploadDisabled(
            files,
            selectedBucket,
            links,
            isUploading,
          )}
          isUploading={isUploading}
          onSubmit={submitUploadData}
        />
      }
      title="Upload Data"
      onClose={onDialogClose}
    >
      <div className="upload-dialog__content">
        <BucketsDropdown
          files={files}
          selectedBucket={selectedBucket}
          onBucketChange={onBucketChange}
        />
        <div className="upload-dialog__ingestion-panels-grid">
          <FilesIngestionPanel files={files} setFiles={setFiles} />
          <LinksIngestionPanel links={links} setLinks={setLinks} />
        </div>
        {isUploading && <div className="upload-dialog__blur-overlay"></div>}
      </div>
    </Dialog>
  );
};
export default UploadDataDialog;
