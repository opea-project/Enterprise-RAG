// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FetchBaseQueryError } from "@reduxjs/toolkit/query/react";

import { UpdatedChatMessage } from "@/features/chat/types";
import {
  HTTP_STATUS,
  OnMessageTextUpdateHandler,
} from "@/features/chat/types/api";
import { transformErrorMessage } from "@/utils/api";

export const handleUnsuccessfulChatResponse = async (response: Response) => {
  if (response.status === HTTP_STATUS.REQUEST_TIMEOUT) {
    throw new Error(`
        Your request took too long to complete.
        Please try again later or contact your administrator if the problem persists.
      `);
  } else if (response.status === HTTP_STATUS.PAYLOAD_TOO_LARGE) {
    throw new Error(`
        Your prompt seems to be too large to be processed.
        Please shorten your prompt and send it again.
        If the issue persists, please contact your administrator.
      `);
  } else if (response.status === HTTP_STATUS.TOO_MANY_REQUESTS) {
    throw new Error(`
        You've reached the limit of requests.
        Please take a short break and try again soon.
      `);
  } else if (response.status === HTTP_STATUS.GUARDRAILS_ERROR) {
    const error = await response.json();
    throw new Error(JSON.stringify(error));
  } else if (!response.ok) {
    throw new Error(
      "An error occurred. Please contact your administrator for further details.",
    );
  }
};

export const handleChatJsonResponse = async (
  response: Response,
  onMessageTextUpdate: OnMessageTextUpdateHandler,
) => {
  const json = await response.json();
  onMessageTextUpdate(json.text);
};

export const handleChatStreamResponse = async (
  response: Response,
  onMessageTextUpdate: OnMessageTextUpdateHandler,
) => {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder("utf-8");

  let done = false;
  while (!done) {
    const result = await reader?.read();
    done = result?.done ?? true;
    if (done) break;

    // decoding streamed events for a given moment in time
    const decodedValue = decoder.decode(result?.value, {
      stream: true,
    });

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

        onMessageTextUpdate(newTextChunk);
      }
    }
  }
};

export const transformChatErrorMessage = (
  error: FetchBaseQueryError,
): FetchBaseQueryError => {
  if (error.status === "PARSING_ERROR") {
    if (error.originalStatus === HTTP_STATUS.GUARDRAILS_ERROR) {
      const data = JSON.parse(JSON.parse(error.data).error).detail;
      return { status: error.originalStatus, data };
    } else {
      return {
        status: error.originalStatus,
        data: error.error,
      };
    }
  }

  return transformErrorMessage(error, "Unknown error occurred");
};

export const getChatErrorMessage = (
  error: unknown,
): string | UpdatedChatMessage => {
  if (typeof error === "object" && error !== null && "error" in error) {
    if (
      typeof error.error === "object" &&
      error.error !== null &&
      "status" in error.error &&
      "data" in error.error &&
      typeof error.error.data === "string"
    ) {
      const { status, data } = error.error;
      if (typeof status === "number") {
        if (status === HTTP_STATUS.GUARDRAILS_ERROR) {
          return data;
        }

        return {
          text: data,
          isError: true,
        };
      } else if (typeof status === "string") {
        if (status === "FETCH_ERROR" && data.includes("AbortError")) {
          return "";
        }

        return {
          text: data,
          isError: true,
        };
      }
    }
  }

  return "";
};
