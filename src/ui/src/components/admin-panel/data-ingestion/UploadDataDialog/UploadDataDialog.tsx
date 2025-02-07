// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadDataDialog.scss";

import { useRef, useState } from "react";

import FilesIngestionPanel from "@/components/admin-panel/data-ingestion/FilesIngestionPanel/FilesIngestionPanel";
import LinksIngestionPanel from "@/components/admin-panel/data-ingestion/LinksIngestionPanel/LinksIngestionPanel";
import UploadDataDialogFooter from "@/components/admin-panel/data-ingestion/UploadDataDialogFooter/UploadDataDialogFooter";
import Button from "@/components/shared/Button/Button";
import Dialog from "@/components/shared/Dialog/Dialog";
import {
  LinkForIngestion,
  UploadErrors,
} from "@/models/admin-panel/data-ingestion/dataIngestion";
import DataIngestionService from "@/services/dataIngestionService";
import { getFiles, getLinks } from "@/store/dataIngestion.slice";
import { useAppDispatch } from "@/store/hooks";
import { addNotification } from "@/store/notifications.slice";
import {
  createToBeUploadedMessage,
  isUploadDisabled,
} from "@/utils/data-ingestion";

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
        await DataIngestionService.postFiles(files);
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
        await DataIngestionService.postLinks(links);
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
      dispatch(getFiles());
      dispatch(getLinks());
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
