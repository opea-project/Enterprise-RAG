// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LinkForIngestion } from "@/types/admin-panel/data-ingestion";

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

export {
  createToBeUploadedMessage,
  formatFileSize,
  formatProcessingTimePeriod,
  isUploadDisabled,
};
