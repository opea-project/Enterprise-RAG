// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadDataDialog.scss";

import { useRef, useState } from "react";

import Button from "@/components/ui/Button/Button";
import Dialog from "@/components/ui/Dialog/Dialog";
import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import {
  useGetFilePresignedUrlMutation,
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

  const ref = useRef<HTMLDialogElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [links, setLinks] = useState<LinkForIngestion[]>([]);
  const [selectedBucket, setSelectedBucket] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadErrors, setUploadErrors] =
    useState<UploadErrors>(initialUploadErrors);

  const dispatch = useAppDispatch();

  const onBucketChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedBucket(event.target.value);
  };

  const resetUploadErrors = () => {
    setUploadErrors(initialUploadErrors);
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
      closeDialog();
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

  const closeDialog = () => {
    if (ref.current) {
      setFiles([]);
      setLinks([]);
      resetUploadErrors();
      ref.current.close();
    }
  };

  const showDialog = () => {
    if (ref.current) {
      ref.current.showModal();
    }
  };

  const triggerButton = (
    <Button icon="upload" onPress={showDialog}>
      Upload
    </Button>
  );

  const toBeUploadedMessage = createToBeUploadedMessage(
    files,
    selectedBucket,
    links,
  );
  const uploadDisabled = isUploadDisabled(
    files,
    selectedBucket,
    links,
    isUploading,
  );

  return (
    <Dialog
      ref={ref}
      trigger={triggerButton}
      footer={
        <UploadDataDialogFooter
          uploadErrors={uploadErrors}
          toBeUploadedMessage={toBeUploadedMessage}
          uploadDisabled={uploadDisabled}
          isUploading={isUploading}
          onSubmit={submitUploadData}
        />
      }
      title="Upload Data"
      onClose={closeDialog}
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
