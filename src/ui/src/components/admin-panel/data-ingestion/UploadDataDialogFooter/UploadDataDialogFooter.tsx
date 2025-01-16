// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadDataDialogFooter.scss";

import { useCallback } from "react";
import { BsCloudUploadFill, BsExclamationCircleFill } from "react-icons/bs";

import Tooltip from "@/components/shared/Tooltip/Tooltip";
import { UploadErrors } from "@/models/admin-panel/data-ingestion/dataIngestion";

interface UploadDataDialogFooterProps {
  uploadErrors: UploadErrors;
  toBeUploadedMessage: string;
  uploadDisabled: boolean;
  isUploading: boolean;
  onSubmit: () => void;
}

const UploadDataDialogFooter = ({
  uploadErrors,
  toBeUploadedMessage,
  uploadDisabled,
  isUploading,
  onSubmit,
}: UploadDataDialogFooterProps) => {
  const hasUploadErrors =
    uploadErrors.files !== "" || uploadErrors.links !== "";

  const getFooterMessage = useCallback(() => {
    if (hasUploadErrors) {
      const tooltipText = (
        <>
          {uploadErrors.files !== "" && <p>Files: {uploadErrors.files}</p>}
          {uploadErrors.links !== "" && <p>Links: {uploadErrors.links}</p>}
        </>
      );
      return (
        <>
          <Tooltip text={tooltipText} position="left">
            <div className="upload-dialog__error">
              <BsExclamationCircleFill className="upload-dialog__error--icon" />
              <p className="upload-dialog__error--text">Error during upload</p>
            </div>
          </Tooltip>
        </>
      );
    }

    return toBeUploadedMessage;
  }, [
    hasUploadErrors,
    uploadErrors.files,
    uploadErrors.links,
    toBeUploadedMessage,
  ]);

  const uploadBtnContent = isUploading ? (
    <>
      <BsCloudUploadFill className="mr-2" />
      <p>Uploading...</p>
    </>
  ) : (
    <p>Upload Data</p>
  );

  return (
    <div className="upload-dialog__footer">
      <p>{getFooterMessage()}</p>
      <button
        className="upload-data__footer--button"
        disabled={uploadDisabled}
        onClick={onSubmit}
      >
        {uploadBtnContent}
      </button>
    </div>
  );
};

export default UploadDataDialogFooter;
