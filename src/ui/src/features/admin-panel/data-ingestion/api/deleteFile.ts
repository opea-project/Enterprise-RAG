// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getFilePresignedUrl } from "@/features/admin-panel/data-ingestion/api/getFilePresignedUrl";
import { refreshToken } from "@/lib/auth";

export const deleteFile = async (
  fileName: string,
  bucketName: string = "default",
) => {
  await refreshToken();

  const method = "DELETE";
  const url = await getFilePresignedUrl(fileName, method, bucketName);

  const response = await fetch(url, {
    method,
  });

  if (!response.ok) {
    throw new Error("Failed to delete file");
  }
};
