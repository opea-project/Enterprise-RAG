// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { parseServiceDetailsResponseData } from "@/features/admin-panel/control-plane/utils";
import { getToken, refreshToken } from "@/lib/auth";

export const getChatQAStatus = async () => {
  await refreshToken();

  try {
    const headers = new Headers();
    headers.append("Authorization", `Bearer ${getToken()}`);
    const response = await fetch("/api/v1/chatqa/status", {
      headers,
    });

    if (response.ok) {
      const servicesData = await response.json();
      return parseServiceDetailsResponseData(servicesData);
    }
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === "SyntaxError") {
        throw new Error("Failed to fetch services statuses");
      } else {
        throw new Error(error.message);
      }
    }
  }
};
