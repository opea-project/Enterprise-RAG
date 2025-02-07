// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadDataDialogFooter.scss";

import UploadErrorsDialog from "@/components/admin-panel/data-ingestion/UploadErrorsDialog/UploadErrorsDialog";
import { IconName } from "@/components/icons";
import Button from "@/components/shared/Button/Button";
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

  const uploadBtnContent = isUploading ? "Uploading..." : "Upload Data";
  const uploadBtnIcon: IconName | undefined = isUploading
    ? "loading"
    : undefined;

  return (
    <div className="upload-dialog__footer">
      {hasUploadErrors ? (
        <UploadErrorsDialog uploadErrors={uploadErrors} />
      ) : (
        toBeUploadedMessage
      )}
      <Button icon={uploadBtnIcon} disabled={uploadDisabled} onClick={onSubmit}>
        {uploadBtnContent}
      </Button>
    </div>
  );
};

export default UploadDataDialogFooter;
