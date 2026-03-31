// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import { LinkForIngestion } from "@/features/admin-panel/data-ingestion/types";

export const parseSharePointError = (error: unknown): string => {
  if (typeof error !== "object" || error === null) {
    return ERROR_MESSAGES.POST_SHAREPOINT_SITE;
  }

  const { status, data } = error as { status?: unknown; data?: unknown };
  const detail =
    typeof data === "object" && data !== null
      ? ((data as { detail?: string }).detail ?? null)
      : null;

  if (
    typeof detail === "string" &&
    detail.toLowerCase().includes("cannot parse hostname")
  ) {
    return "Invalid URL format. Please enter a valid SharePoint site URL.";
  }

  if (status === 403) {
    return "Access denied. The application does not have permission to access this SharePoint site.";
  }

  if (status === 400) {
    return "The provided URL does not point to a valid SharePoint site.";
  }

  if (typeof detail === "string") {
    return detail;
  }

  return ERROR_MESSAGES.POST_SHAREPOINT_SITE;
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

export { createToBeUploadedMessage, isUploadDisabled };
