// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadDataDialog.scss";

import { useRef, useState } from "react";

import Button from "@/components/ui/Button/Button";
import Dialog from "@/components/ui/Dialog/Dialog";
import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { postFiles } from "@/features/admin-panel/data-ingestion/api/postFiles";
import { postLinks } from "@/features/admin-panel/data-ingestion/api/postLinks";
import FilesIngestionPanel from "@/features/admin-panel/data-ingestion/components/FilesIngestionPanel/FilesIngestionPanel";
import LinksIngestionPanel from "@/features/admin-panel/data-ingestion/components/LinksIngestionPanel/LinksIngestionPanel";
import UploadDataDialogFooter from "@/features/admin-panel/data-ingestion/components/UploadDataDialogFooter/UploadDataDialogFooter";
import {
  fetchFiles,
  fetchLinks,
} from "@/features/admin-panel/data-ingestion/store/dataIngestion.slice";
import {
  LinkForIngestion,
  UploadErrors,
} from "@/features/admin-panel/data-ingestion/types";
import {
  createToBeUploadedMessage,
  isUploadDisabled,
} from "@/features/admin-panel/data-ingestion/utils";
import { useAppDispatch } from "@/store/hooks";

const initialUploadErrors = {
  files: "",
  links: "",
};

const UploadDataDialog = () => {
  const ref = useRef<HTMLDialogElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [links, setLinks] = useState<LinkForIngestion[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadErrors, setUploadErrors] =
    useState<UploadErrors>(initialUploadErrors);

  const dispatch = useAppDispatch();

  const resetUploadErrors = () => {
    setUploadErrors(initialUploadErrors);
  };

  const submitUploadData = async () => {
    resetUploadErrors();
    setIsUploading(true);

    let filesUploadError = "";
    let linksUploadError = "";

    try {
      if (files.length) {
        await postFiles(files);
        setFiles([]);
      }
    } catch (error) {
      filesUploadError =
        error instanceof Error
          ? error.message
          : "Unknown error occurred during files upload";
    }

    try {
      if (links.length) {
        await postLinks(links);
        setLinks([]);
      }
    } catch (error) {
      linksUploadError =
        error instanceof Error
          ? error.message
          : "Unknown error occurred during links upload";
    }

    if (filesUploadError || linksUploadError) {
      setUploadErrors({
        links: linksUploadError,
        files: filesUploadError,
      });
    } else {
      closeDialog();
      dispatch(
        addNotification({
          text: "Successful data upload!",
          severity: "success",
        }),
      );
      dispatch(fetchFiles());
      dispatch(fetchLinks());
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
    <Button icon="upload" onClick={showDialog}>
      Upload
    </Button>
  );

  const toBeUploadedMessage = createToBeUploadedMessage(files, links);
  const uploadDisabled = isUploadDisabled(files, links, isUploading);

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
      <div className="upload-dialog__ingestion-panels-grid">
        <FilesIngestionPanel files={files} setFiles={setFiles} />
        <LinksIngestionPanel links={links} setLinks={setLinks} />
        {isUploading && <div className="upload-dialog__blur-overlay"></div>}
      </div>
    </Dialog>
  );
};
export default UploadDataDialog;
