// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DataStatus } from "@/features/admin-panel/data-ingestion/types";

export const API_ENDPOINTS = {
  BASE_URL: "/api/v1/edp",
  GET_FILES: "/files",
  GET_FILE_PRESIGNED_URL: "/presignedUrl",
  RETRY_FILE_ACTION: "/file/{uuid}/retry",
  POST_FILE_TO_EXTRACT_TEXT: "/file/{uuid}/extract",
  POST_LINK_TO_EXTRACT_TEXT: "/link/{uuid}/extract",
  GET_FILES_SYNC: "/files/sync",
  POST_FILES_SYNC: "/files/sync",

  GET_LINKS: "/links",
  POST_LINKS: "/links",
  RETRY_LINK_ACTION: "/link/{uuid}/retry",
  DELETE_LINK: "/link/{uuid}",

  GET_S3_BUCKETS_LIST: "/list_buckets",
} as const;

export const ERROR_MESSAGES = {
  GET_FILES: "Failed to fetch files",
  POST_FILE: "Failed to upload file:",
  POST_FILES: "Failed to upload files",
  GET_FILE_PRESIGNED_URL: "Failed to get presigned URL for file",
  DOWNLOAD_FILE: "Failed to download file",
  RETRY_FILE_ACTION: "Error occurred when retrying file action",
  DELETE_FILE: "Failed to delete file",
  POST_FILE_TO_EXTRACT_TEXT: "Failed to extract text from the file",
  POST_LINK_TO_EXTRACT_TEXT: "Failed to extract text from the link",
  GET_FILES_SYNC: "Failed to fetch files synchronization status",
  POST_FILES_SYNC: "Failed to synchronize files",

  GET_LINKS: "Failed to fetch links",
  POST_LINKS: "Failed to upload links",
  RETRY_LINK_ACTION: "Failed to retry link action",
  DELETE_LINK: "Failed to delete link",

  GET_S3_BUCKETS_LIST: "Failed to fetch S3 buckets list",
} as const;

export const END_DATA_STATUSES: DataStatus[] = [
  "error",
  "ingested",
  "canceled",
  "blocked",
];

export const POLLING_INTERVAL = 10000; // 10 seconds
