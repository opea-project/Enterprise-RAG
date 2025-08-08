// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const API_ENDPOINTS = {
  GET_FILE_PRESIGNED_URL: "/api/v1/edp/presignedUrl",
} as const;

export const ERROR_MESSAGES = {
  GET_FILE_PRESIGNED_URL: "Failed to get presigned URL for file",
  DOWNLOAD_FILE: "Failed to download file",
} as const;
