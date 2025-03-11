// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getFilePresignedUrl } from "@/features/admin-panel/data-ingestion/api/getFilePresignedUrl";
import { refreshToken } from "@/lib/auth";

export const postFiles = async (files: File[]) => {
  await refreshToken();

  for (const file of files) {
    const method = "PUT";
    const url = await getFilePresignedUrl(file.name, method);

    const response = await fetch(url, {
      method,
      body: file,
      headers: {
        "Content-Type": file.type,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to upload file: ${file.name}`);
    }
  }
};
