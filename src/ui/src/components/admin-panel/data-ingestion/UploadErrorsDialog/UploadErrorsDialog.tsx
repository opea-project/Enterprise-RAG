// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadErrorsDialog.scss";

import { useRef } from "react";
import { BsExclamationCircleFill } from "react-icons/bs";

import Anchor from "@/components/shared/Anchor/Anchor";
import Dialog from "@/components/shared/Dialog/Dialog";
import { UploadErrors } from "@/models/admin-panel/data-ingestion/dataIngestion";

const s3Url = import.meta.env.VITE_S3_URL;

const UndeterminedNetworkErrorMessage = (
  <p>
    The upload failed for an undetermined network reason. This issue may occur
    due to certificate that the browser does not trust.
    <br />
    If you are using self-signed or custom certificate, open the URL below and
    accept the certificate. After doing this, close this popup and retry upload.
    <br />
    <Anchor href={s3Url}>{s3Url}</Anchor>
  </p>
);

interface UploadErrorsDialogProps {
  uploadErrors: UploadErrors;
}

const UploadErrorsDialog = ({ uploadErrors }: UploadErrorsDialogProps) => {
  const ref = useRef<HTMLDialogElement>(null);

  const handleClose = () => ref.current?.close();

  const showDialog = () => ref.current?.showModal();

  const trigger = (
    <div className="upload-errors-dialog__trigger" onClick={showDialog}>
      <BsExclamationCircleFill className="upload-errors-dialog__trigger--icon" />
      <p className="upload-errors-dialog__trigger--text">Error during upload</p>
    </div>
  );

  const getUploadErrors = (dataType: "links" | "files") => {
    if (uploadErrors[dataType] === "") {
      return null;
    }

    const isUndeterminedNetworkError =
      uploadErrors[dataType].includes("Failed to fetch");

    const sectionTitle = `${dataType[0].toUpperCase()}${dataType.slice(1)}`;

    return (
      <section className="upload-errors-dialog__section">
        <h4>{sectionTitle}</h4>
        <p>{uploadErrors[dataType]}</p>
        {isUndeterminedNetworkError && UndeterminedNetworkErrorMessage}
      </section>
    );
  };

  return (
    <Dialog
      ref={ref}
      trigger={trigger}
      title="Error during upload"
      onClose={handleClose}
    >
      {getUploadErrors("files")}
      {getUploadErrors("links")}
    </Dialog>
  );
};

export default UploadErrorsDialog;
