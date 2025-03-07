// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import endpoints from "@/api/endpoints.json";
import {
  AppendArgumentsRequestBody,
  ChangeArgumentsRequestBody,
} from "@/api/models/systemFingerprint";
import keycloakService from "@/services/keycloakService";
import {
  parseServiceDetailsResponseData,
  parseServicesParameters,
} from "@/utils";

class SystemFingerprintService {
  async appendArguments() {
    await keycloakService.refreshToken();

    const url = endpoints.systemFingerprint.appendArguments;
    const body: AppendArgumentsRequestBody = { text: "" };
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (response.ok) {
      const { parameters } = await response.json();
      return parseServicesParameters(parameters);
    } else {
      throw new Error("Failed to fetch service arguments");
    }
  }
  async changeArguments(requestBody: ChangeArgumentsRequestBody) {
    await keycloakService.refreshToken();

    const url = endpoints.systemFingerprint.changeArguments;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (response.ok) {
      return await response.json();
    } else {
      throw new Error("Failed to change service arguments");
    }
  }

  async getChatQnAServiceDetails() {
    await keycloakService.refreshToken();

    const url = endpoints.systemFingerprint.chatqnaStatus;

    try {
      const response = await fetch(url, {
        headers: {
          Authorization: `${keycloakService.getToken()}`,
        },
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
  }
}

export default new SystemFingerprintService();
