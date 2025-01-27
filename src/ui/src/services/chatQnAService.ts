// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PayloadAction } from "@reduxjs/toolkit";

import endpoints from "@/api/endpoints.json";
import keycloakService from "@/services/keycloakService";
import {
  updateBotMessageText,
  UpdatedChatMessage,
} from "@/store/conversationFeed.slice";

class ChatQnAService {
  async postPrompt(
    prompt: string,
    abortSignal: AbortSignal,
    dispatch: (action: PayloadAction<string | UpdatedChatMessage>) => void,
  ) {
    await keycloakService.refreshToken();

    const body = JSON.stringify({
      text: prompt,
    });

    const response = await fetch(endpoints.chatQnA.postPrompt, {
      method: "POST",
      body,
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
      },
      signal: abortSignal,
    });

    if (response.status === 408) {
      // 408 - Request timeout
      throw new Error(`
        Your request took too long to complete.
        Please try again later or contact your administrator if the problem persists.
      `);
    } else if (response.status === 413) {
      // 413 - Payload Too Large
      throw new Error(`
        Your prompt seems to be too large to be processed.
        Please shorten your prompt and send it again.
        If the issue persists, please contact your administrator.
      `);
    } else if (response.status === 429) {
      // 413 - Too Many Requests
      throw new Error(`
        You've reached the limit of requests.
        Please take a short break and try again soon.
      `);
    } else if (response.status === 466) {
      // 466 - Custom Error - Guardrails
      const error = await response.json();
      throw new Error(`Guard: ${JSON.stringify(error)}`);
    } else if (!response.ok) {
      // Handle all other errors that are not strictly related to user's prompt and actions
      throw new Error(
        "An error occurred. Please contact your administrator for further details.",
      );
    }

    const contentType = response.headers.get("Content-Type");
    if (contentType && contentType.includes("application/json")) {
      const json = await response.json();
      dispatch(updateBotMessageText(json.text));
    } else if (contentType && contentType.includes("text/event-stream")) {
      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");

      let done = false;
      while (!done) {
        const result = await reader?.read();
        done = result?.done ?? true;
        if (done) break;

        // decoding streamed events for a given moment in time
        const decodedValue = decoder.decode(result?.value, { stream: true });

        // in case of streaming multiple events at one time - configuration with output guard
        const events = decodedValue.split("\n\n");

        for (const event of events) {
          if (event.startsWith("data:")) {
            // skip to the next iteration if event data message is a keyword indicating that stream has finished
            if (event.includes("[DONE]") || event.includes("</s>")) {
              continue;
            }

            // extract chunk of text from event data message
            let newTextChunk = event.slice(5).trim();
            let quoteRegex = /(?<!\\)'/g;
            if (newTextChunk.startsWith('"')) {
              quoteRegex = /"/g;
            }
            newTextChunk = newTextChunk
              .replace(quoteRegex, "")
              .replace(/\\n/, "  \n");

            dispatch(updateBotMessageText(newTextChunk));
          }
        }
      }
    } else {
      throw new Error(
        "Response from chat cannot be processed - Unsupported Content-Type",
      );
    }
  }
}

export default new ChatQnAService();
