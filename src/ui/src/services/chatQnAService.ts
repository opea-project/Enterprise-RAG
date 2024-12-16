// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  EventSourceMessage,
  fetchEventSource,
} from "@microsoft/fetch-event-source";

import endpoints from "@/api/endpoints.json";
import { PromptRequestParams } from "@/api/models/chatQnA";
import keycloakService from "@/services/keycloakService";
import { parsePromptRequestParameters } from "@/utils";

class ChatQnAService {
  async getPromptRequestParams(
    hasInputGuard: boolean,
    hasOutputGuard: boolean,
  ) {
    await keycloakService.refreshToken();

    const body = JSON.stringify({ text: "" });

    const response = await fetch(endpoints.chatQnA.getPromptRequestParams, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
        "Content-Type": "application/json",
      },
      body,
    });

    if (response.ok) {
      const { parameters } = await response.json();
      const promptRequestParams = parsePromptRequestParameters(
        parameters,
        hasInputGuard,
        hasOutputGuard,
      );
      return promptRequestParams;
    } else {
      throw new Error("Failed to get prompt request parameters");
    }
  }

  async postPromptForBufferedResponse(
    prompt: string,
    promptRequestParams: PromptRequestParams,
    abortSignal: AbortSignal,
  ) {
    await keycloakService.refreshToken();

    const body = JSON.stringify({
      text: prompt,
      parameters: promptRequestParams,
    });

    const response = await fetch(endpoints.chatQnA.postPrompt, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
      },
      body,
      signal: abortSignal,
    });

    const data = await response.json();
    if (!data.text) {
      throw new Error("Failed to get response from chat");
    }
    return data.text;
  }

  async postPromptForStreamedResponse(
    prompt: string,
    promptRequestParams: PromptRequestParams,
    abortSignal: AbortSignal,
    onMessageHandler: (event: EventSourceMessage) => void,
  ) {
    await keycloakService.refreshToken();

    const body = JSON.stringify({
      text: prompt,
      parameters: promptRequestParams,
    });

    await fetchEventSource(endpoints.chatQnA.postPrompt, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
      },
      body,
      signal: abortSignal,
      openWhenHidden: true,
      onopen: async (response) => {
        if (response.ok) {
          return;
        } else if (
          response.status >= 400 &&
          response.status < 500 &&
          response.status !== 429
        ) {
          const error = await response.json();
          let msg = JSON.stringify(error);
          if (response.status === 466) {
            // Guardrails
            msg = `Guard: ${msg}`;
          }
          throw new Error(msg);
        } else {
          throw new Error("Opening connection failed");
        }
      },
      onmessage: onMessageHandler,
      onerror: (err) => {
        throw new Error(err);
      },
    });
  }
}

export default new ChatQnAService();
