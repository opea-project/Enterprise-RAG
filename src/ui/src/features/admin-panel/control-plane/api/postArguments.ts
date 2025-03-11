// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeArgumentsRequestBody } from "@/features/admin-panel/control-plane/types/systemFingerprint";
import { getToken, refreshToken } from "@/lib/auth";

export const postArguments = async (
  requestBody: ChangeArgumentsRequestBody,
) => {
  await refreshToken();

  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);
  headers.append("Content-Type", "application/json");
  const response = await fetch("/v1/system_fingerprint/change_arguments", {
    method: "POST",
    headers,
    body: JSON.stringify(requestBody),
  });

  if (response.ok) {
    return await response.json();
  } else {
    throw new Error("Failed to change service arguments");
  }
};
