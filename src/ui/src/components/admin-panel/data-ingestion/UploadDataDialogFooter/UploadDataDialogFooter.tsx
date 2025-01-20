// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadDataDialogFooter.scss";

import { BsCloudUploadFill } from "react-icons/bs";

import { UploadErrors } from "@/models/admin-panel/data-ingestion/dataIngestion";

import UploadErrorsDialog from "../UploadErrorsDialog/UploadErrorsDialog";

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
      {hasUploadErrors ? (
        <UploadErrorsDialog uploadErrors={uploadErrors} />
      ) : (
        toBeUploadedMessage
      )}
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
