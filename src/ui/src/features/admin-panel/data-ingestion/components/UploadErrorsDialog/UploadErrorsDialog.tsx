// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadErrorsDialog.scss";

import ErrorIcon from "@/components/icons/ErrorIcon/ErrorIcon";
import Anchor from "@/components/ui/Anchor/Anchor";
import Popup from "@/components/ui/Popup/Popup";
import { UploadErrors } from "@/features/admin-panel/data-ingestion/types";
import { getAppEnv, titleCaseString } from "@/utils";

const s3Url = getAppEnv("S3_URL");

const UndeterminedNetworkErrorMessage = (
  <>
    <p>
      The upload failed for an undetermined network reason. This issue may occur
      due to certificate that the browser does not trust.
    </p>
    <p>
      If you are using self-signed or custom certificate, open the URL below and
      accept the certificate. After doing this, click outside this popup and
      retry upload.
    </p>
    <Anchor href={s3Url}>{s3Url}</Anchor>
  </>
);

interface UploadErrorsDialogProps {
  uploadErrors: UploadErrors;
}

const UploadErrorsDialog = ({ uploadErrors }: UploadErrorsDialogProps) => {
  const trigger = (
    <div className="upload-errors-dialog__trigger">
      <ErrorIcon className="upload-errors-dialog__trigger--icon" />
      <p className="upload-errors-dialog__trigger--text">Error during upload</p>
    </div>
  );

  const getUploadErrors = (dataType: "links" | "files") => {
    if (uploadErrors[dataType] === "") {
      return null;
    }

    const isUndeterminedNetworkError =
      uploadErrors[dataType].includes("Failed to upload");

    const sectionTitle = titleCaseString(dataType);

    return (
      <section className="upload-errors-dialog__section">
        <h4>{sectionTitle}</h4>
        <p>{uploadErrors[dataType]}</p>
        {isUndeterminedNetworkError && UndeterminedNetworkErrorMessage}
      </section>
    );
  };

  return (
    <Popup popupTrigger={trigger} placement="top end">
      {getUploadErrors("files")}
      {getUploadErrors("links")}
    </Popup>
  );
};

export default UploadErrorsDialog;
