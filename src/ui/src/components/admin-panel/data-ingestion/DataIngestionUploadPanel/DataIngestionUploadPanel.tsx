// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionUploadPanel.scss";

import { BsCloudUploadFill } from "react-icons/bs";

import { LinkForIngestion } from "@/models/admin-panel/data-ingestion/dataIngestion";

interface DataIngestionUploadPanelProps {
  documents: File[];
  links: LinkForIngestion[];
  onUploadBtnClick: () => void;
  isUploading: boolean;
}

const createUploadedDataMessage = (
  documents: File[],
  links: LinkForIngestion[],
) => {
  let message = "";
  if (documents.length > 0) {
    message += `${documents.length} document${documents.length > 1 ? "s" : ""} `;
  }
  if (documents.length > 0 && links.length > 0) {
    message += "and ";
  }
  if (links.length > 0) {
    message += `${links.length} link${links.length > 1 ? "s" : ""}`;
  }
  if (documents.length > 0 || links.length > 0) {
    message += " to be uploaded";
  }
  return message;
};

const isUploadDataButtonDisabled = (
  documents: File[],
  links: LinkForIngestion[],
  isUploading: boolean,
) => isUploading || (documents.length === 0 && links.length === 0);

const DataIngestionUploadPanel = ({
  documents,
  links,
  onUploadBtnClick,
  isUploading,
}: DataIngestionUploadPanelProps) => {
  const uploadedDataMessage = createUploadedDataMessage(documents, links);

  const uploadDataButtonDisabled = isUploadDataButtonDisabled(
    documents,
    links,
    isUploading,
  );

  return (
    <div className="upload-data-panel">
      {uploadedDataMessage !== "" && <p>{uploadedDataMessage}</p>}
      <button
        className="upload-data-button"
        disabled={uploadDataButtonDisabled}
        onClick={onUploadBtnClick}
      >
        {isUploading ? (
          <>
            <BsCloudUploadFill className="mr-2" />
            <p>Uploading...</p>
          </>
        ) : (
          "Upload Data"
        )}
      </button>
    </div>
  );
};

export default DataIngestionUploadPanel;
