// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LinkForIngestion } from "@/features/admin-panel/data-ingestion/types";
import { getToken, refreshToken } from "@/lib/auth";

export const postLinks = async (linksForIngestion: LinkForIngestion[]) => {
  await refreshToken();

  const links = linksForIngestion.map(({ value }) => value);
  const body = JSON.stringify({ links });
  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);
  headers.append("Content-Type", "application/json");
  const response = await fetch("/api/v1/edp/links", {
    method: "POST",
    body,
    headers,
  });

  if (!response.ok) {
    const errorResponse = await response.json();
    const errorMessage = errorResponse.detail ?? "Failed to post links";
    throw new Error(errorMessage);
  }
};
