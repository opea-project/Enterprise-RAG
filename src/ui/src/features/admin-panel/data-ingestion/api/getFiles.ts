// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getToken, refreshToken } from "@/lib/auth";

export const getFiles = async () => {
  await refreshToken();

  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);
  const response = await fetch("/api/v1/edp/files", {
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch links");
  } else {
    return await response.json();
  }
};
