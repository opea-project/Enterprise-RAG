// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadDataDialogFooter.scss";

import { IconName } from "@/components/icons";
import Button from "@/components/ui/Button/Button";
import UploadErrorsDialog from "@/features/admin-panel/data-ingestion/components/UploadErrorsDialog/UploadErrorsDialog";
import { UploadErrors } from "@/features/admin-panel/data-ingestion/types";

interface UploadDataDialogFooterProps {
  uploadErrors: UploadErrors;
  toBeUploadedMessage: string;
  isUploadDisabled: boolean;
  isUploading: boolean;
  onSubmit: () => void;
}

const UploadDataDialogFooter = ({
  uploadErrors,
  toBeUploadedMessage,
  isUploadDisabled,
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
      <Button
        icon={uploadBtnIcon}
        isDisabled={isUploadDisabled}
        onPress={onSubmit}
      >
        {uploadBtnContent}
      </Button>
    </div>
  );
};

export default UploadDataDialogFooter;
