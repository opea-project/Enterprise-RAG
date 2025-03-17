// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getToken, refreshToken } from "@/lib/auth";

export const getS3BucketsList = async () => {
  await refreshToken();

  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);
  headers.append("Content-Type", "application/json");

  const response = await fetch("/api/v1/edp/list_buckets", {
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch S3 buckets list");
  }

  const responseData = await response.json();

  return responseData.buckets ?? [];
};
