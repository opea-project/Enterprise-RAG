// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LinkForIngestion } from "@/features/admin-panel/data-ingestion/types";

const createToBeUploadedMessage = (
  files: File[],
  selectedBucket: string,
  links: LinkForIngestion[],
) => {
  let message = "";
  if (files.length > 0 && selectedBucket !== "") {
    message += `${files.length} file${files.length > 1 ? "s" : ""} `;
  }
  if (files.length > 0 && selectedBucket !== "" && links.length > 0) {
    message += "and ";
  }
  if (links.length > 0) {
    message += `${links.length} link${links.length > 1 ? "s" : ""}`;
  }
  if ((files.length > 0 && selectedBucket !== "") || links.length > 0) {
    message += " to be uploaded";
  }
  return message;
};

const isUploadDisabled = (
  files: File[],
  selectedBucket: string,
  links: LinkForIngestion[],
  isUploading: boolean,
) => {
  if (isUploading) {
    return true;
  }

  const areFilesReadyToUpload = files.length > 0 && selectedBucket !== "";
  const areLinksReadyToUpload = links.length > 0;

  return !areFilesReadyToUpload && !areLinksReadyToUpload;
};

export { createToBeUploadedMessage, isUploadDisabled };
