// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getToken, refreshToken } from "@/lib/auth";

export const deleteLink = async (uuid: string) => {
  await refreshToken();

  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);
  const response = await fetch(`/api/v1/edp/link/${uuid}`, {
    method: "DELETE",
    headers,
  });

  if (!response.ok) {
    const errorResponse = await response.json();
    const errorMessage = errorResponse.detail ?? "Error when deleting link";
    throw new Error(errorMessage);
  }
};
