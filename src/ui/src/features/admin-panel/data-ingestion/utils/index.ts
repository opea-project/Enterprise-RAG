// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LinkForIngestion } from "@/features/admin-panel/data-ingestion/types";
import {
  filenameMaxLength,
  filenameUnsafeCharsRegex,
} from "@/features/admin-panel/data-ingestion/utils/constants";

const formatFileSize = (fileSize: number) => {
  const units = ["B", "KB", "MB", "GB", "TB"];

  if (fileSize === 0) {
    return "0 B";
  }
  const n = 1024;
  const i = Math.floor(Math.log(fileSize) / Math.log(n));
  let size: number | string = parseFloat(String(fileSize / Math.pow(n, i)));
  if (fileSize > n) {
    size = size.toFixed(1);
  }

  const unit = units[i];
  return `${size} ${unit}`;
};

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

const sanitizeFileName = (filename: string) => {
  const normalizedFileName = filename.normalize("NFKC");
  const sanitizedFileName = normalizedFileName.replace(
    filenameUnsafeCharsRegex,
    "_",
  );
  const truncatedFileName = sanitizedFileName.substring(0, filenameMaxLength);

  // Encode/decode cycle helps expose homoglyphs and unusual characters
  return decodeURIComponent(encodeURIComponent(truncatedFileName));
};

const sanitizeFiles = (files: File[]): File[] =>
  files.map((file) => {
    const sanitizedFileName = sanitizeFileName(file.name);
    return new File([file], sanitizedFileName, { type: file.type });
  });

export {
  createToBeUploadedMessage,
  formatFileSize,
  isUploadDisabled,
  sanitizeFiles,
};
