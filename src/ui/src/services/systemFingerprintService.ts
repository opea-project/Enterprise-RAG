// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import endpoints from "@/api/endpoints.json";
import {
  AppendArgumentsRequestBody,
  ChangeArgumentsRequestBody,
} from "@/api/models/systemFingerprint";
import { parseServiceDetailsResponseData } from "@/utils";

class SystemFingerprintService {
  async appendArguments() {
    const url = endpoints.systemFingerprint.appendArguments;
    const body: AppendArgumentsRequestBody = { text: "" };

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        const { parameters } = await response.json();
        return parameters;
      } else {
        throw new Error("Failed to fetch arguments");
      }
    } catch (e) {
      console.error(e);
    }
  }
  async changeArguments(requestBody: ChangeArgumentsRequestBody) {
    const url = endpoints.systemFingerprint.changeArguments;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        return await response.json();
      } else {
        throw new Error("Failed to change arguments");
      }
    } catch (e) {
      console.error(e);
    }
  }

  async getChatQnAServiceDetails() {
    const url = endpoints.systemFingerprint.chatqnaStatus;

    try {
      const response = await fetch(url);

      if (response.ok) {
        const servicesData = await response.json();
        return parseServiceDetailsResponseData(servicesData);
      } else {
        throw new Error("Failed to fetch ChatQnA services status");
      }
    } catch (e) {
      console.error(e);
    }
  }
}

export default new SystemFingerprintService();
