// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import endpoints from "@/api/endpoints.json";
import {
  AppendArgumentsRequestBody,
  ChangeArgumentsRequestBody,
} from "@/api/models/systemFingerprint";

class SystemFingerprintService {
  async appendArguments() {
    const url =
      window.location.origin + endpoints.systemFingerprint.appendArguments;
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
    const url =
      window.location.origin + endpoints.systemFingerprint.changeArguments;

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
}

export default new SystemFingerprintService();
