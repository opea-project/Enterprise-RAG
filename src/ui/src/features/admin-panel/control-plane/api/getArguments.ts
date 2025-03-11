// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { parseServicesParameters } from "@/features/admin-panel/control-plane/utils";
import { getToken, refreshToken } from "@/lib/auth";

export const getArguments = async () => {
  await refreshToken();

  const body = { text: "" };
  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);
  headers.append("Content-Type", "application/json");
  const response = await fetch("/v1/system_fingerprint/append_arguments", {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (response.ok) {
    const { parameters } = await response.json();
    return parseServicesParameters(parameters);
  } else {
    throw new Error("Failed to fetch service arguments");
  }
};
