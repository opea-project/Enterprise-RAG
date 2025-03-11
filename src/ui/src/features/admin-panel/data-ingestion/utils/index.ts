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

const formatProcessingTimePeriod = (processingDuration: number) => {
  const hours = Math.floor(processingDuration / 3600);
  const minutes = Math.floor((processingDuration % 3600) / 60);
  const seconds = processingDuration % 60;

  const formattedDuration = [
    hours.toString().padStart(2, "0"),
    minutes.toString().padStart(2, "0"),
    seconds.toString().padStart(2, "0"),
  ].join(":");

  return formattedDuration;
};

const createToBeUploadedMessage = (
  files: File[],
  links: LinkForIngestion[],
) => {
  let message = "";
  if (files.length > 0) {
    message += `${files.length} file${files.length > 1 ? "s" : ""} `;
  }
  if (files.length > 0 && links.length > 0) {
    message += "and ";
  }
  if (links.length > 0) {
    message += `${links.length} link${links.length > 1 ? "s" : ""}`;
  }
  if (files.length > 0 || links.length > 0) {
    message += " to be uploaded";
  }
  return message;
};

const isUploadDisabled = (
  files: File[],
  links: LinkForIngestion[],
  isUploading: boolean,
) => isUploading || (files.length === 0 && links.length === 0);

const sanitizeFileName = (filename: string) => {
  const normalizedFileName = filename.normalize("NFKC");
  const sanitizedFileName = normalizedFileName.replace(
    filenameUnsafeCharsRegex,
    "_",
  );
  const truncatedFileName = sanitizedFileName.substring(0, filenameMaxLength);
  const encodedFileName = encodeURIComponent(truncatedFileName);
  return encodedFileName;
};

const sanitizeFiles = (files: File[]): File[] =>
  files.map((file) => {
    const sanitizedFileName = sanitizeFileName(file.name);
    return new File([file], sanitizedFileName, { type: file.type });
  });

export {
  createToBeUploadedMessage,
  formatFileSize,
  formatProcessingTimePeriod,
  isUploadDisabled,
  sanitizeFiles,
};
