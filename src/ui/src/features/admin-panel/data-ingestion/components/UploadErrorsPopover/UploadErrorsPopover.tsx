// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadErrorsPopover.scss";

import ErrorIcon from "@/components/icons/ErrorIcon/ErrorIcon";
import Anchor from "@/components/ui/Anchor/Anchor";
import Popover from "@/components/ui/Popover/Popover";
import usePopover from "@/components/ui/Popover/usePopover";
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
      accept the certificate. After doing this, click outside this popover and
      retry upload.
    </p>
    <Anchor href={s3Url}>{s3Url}</Anchor>
  </>
);

interface UploadErrorsPopoverProps {
  uploadErrors: UploadErrors;
}

const UploadErrorsPopover = ({ uploadErrors }: UploadErrorsPopoverProps) => {
  const { triggerRef, isOpen, togglePopover } = usePopover<HTMLDivElement>();

  const getUploadErrors = (dataType: "links" | "files") => {
    if (uploadErrors[dataType] === "") {
      return null;
    }

    const isUndeterminedNetworkError =
      uploadErrors[dataType].includes("Failed to upload");

    const sectionTitle = titleCaseString(dataType);

    return (
      <section className="upload-errors-popover__section">
        <h4>{sectionTitle}</h4>
        <p>{uploadErrors[dataType]}</p>
        {isUndeterminedNetworkError && UndeterminedNetworkErrorMessage}
      </section>
    );
  };

  return (
    <>
      <div
        ref={triggerRef}
        className="upload-errors-popover__trigger"
        onClick={togglePopover}
      >
        <ErrorIcon className="upload-errors-popover__trigger--icon" />
        <p className="upload-errors-popover__trigger--text">
          Error during upload
        </p>
      </div>
      <Popover
        isOpen={isOpen}
        triggerRef={triggerRef}
        placement="top end"
        ariaLabel="Upload Errors"
        onOpenChange={togglePopover}
      >
        {getUploadErrors("files")}
        {getUploadErrors("links")}
      </Popover>
    </>
  );
};

export default UploadErrorsPopover;
