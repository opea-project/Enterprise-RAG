// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import endpoints from "@/api/endpoints.json";
import { AppendArgumentsRequest } from "@/api/models/system-fingerprint/appendArguments";
import { ChangeArgumentsRequestBody } from "@/api/models/system-fingerprint/changeArguments";

class SystemFingerprintService {
  async appendArguments() {
    const url =
      window.location.origin + endpoints.systemFingerprint.appendArguments;
    const body: AppendArgumentsRequest = { text: "" };

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      const responseData = await response.json();

      if (response.ok) {
        const { parameters } = responseData;
        delete parameters?.input_guardrail_params;
        delete parameters?.output_guardrail_params;
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
      const responseData = await response.json();

      if (response.ok) {
        return responseData;
      } else {
        throw new Error("Failed to change arguments");
      }
    } catch (e) {
      console.error(e);
    }
  }
}

export default new SystemFingerprintService();
