// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getToken, refreshToken } from "@/lib/auth";

export const getFilePresignedUrl = async (
  fileName: string,
  method: "GET" | "PUT" | "DELETE",
  bucketName: string = "default",
) => {
  await refreshToken();

  const body = JSON.stringify({
    object_name: fileName,
    method,
    bucket_name: bucketName,
  });
  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);
  headers.append("Content-Type", "application/json");
  const response = await fetch("/api/v1/edp/presignedUrl", {
    method: "POST",
    body,
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to get presigned URL for file: ${fileName}`);
  }

  const { url } = await response.json();
  return url;
};
