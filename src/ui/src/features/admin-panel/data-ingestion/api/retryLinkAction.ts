// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getToken, refreshToken } from "@/lib/auth";
import { constructUrlWithUuid } from "@/utils";

export const retryLinkAction = async (uuid: string) => {
  await refreshToken();

  const url = constructUrlWithUuid("/api/v1/edp/link/{uuid}/retry", uuid);
  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);

  const response = await fetch(url, {
    method: "POST",
    headers,
  });

  if (!response.ok) {
    const errorResponse = await response.json();
    const errorMessage =
      errorResponse.detail ?? "Error when retrying link action";
    throw new Error(errorMessage);
  }
};
