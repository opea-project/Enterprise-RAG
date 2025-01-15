// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { EventSourceMessage } from "@microsoft/fetch-event-source";
import { PayloadAction } from "@reduxjs/toolkit";

import { PromptRequestParams } from "@/api/models/chatQnA";
import ChatQnAService from "@/services/chatQnAService";
import { updateBotMessageText } from "@/store/conversationFeed.slice";

export const extractGuardError = (errorString: string): string | null => {
  try {
    // Extract the JSON part from the error string
    const jsonMatch = errorString.match(/Guard: ({.*})/);
    if (!jsonMatch || jsonMatch.length < 2) {
      throw new Error("Guard error occurred but couldn't extract its details.");
    }

    // Parse the extracted JSON
    const errorJson = JSON.parse(jsonMatch[1]);

    // Extract the detail field
    const detailJson = JSON.parse(errorJson.error);
    if (detailJson.detail) {
      return detailJson.detail;
    } else {
      throw new Error();
    }
  } catch (error) {
    console.error("Failed to extract detail:", error);
    if (error instanceof Error) {
      return error.message;
    } else {
      return JSON.stringify(error);
    }
  }
};

export const handleError = (error: unknown): string => {
  if (typeof error === "string") {
    return error;
  }

  if (error instanceof Error) {
    if (error.message.includes("Guard:")) {
      const errorDetails = extractGuardError(error.message);
      return errorDetails ?? error.message;
    } else {
      return error.message;
    }
  } else {
    return JSON.stringify(error);
  }
};

export const handleStreamedResponse = async (
  prompt: string,
  promptRequestParams: PromptRequestParams,
  abortSignal: AbortSignal,
  dispatch: (action: PayloadAction<string>) => void,
) => {
  const onMessageHandler = (event: EventSourceMessage) => {
    if (event.data) {
      if (["'</s>'", "[DONE]"].includes(event.data)) {
        return;
      }

      let newTextChunk = event.data;
      let quoteRegex = /(?<!\\)'/g;
      if (newTextChunk.startsWith('"')) {
        quoteRegex = /"/g;
      }
      newTextChunk = newTextChunk
        .replace(quoteRegex, "")
        .replace(/\\n/, "  \n");

      dispatch(updateBotMessageText(newTextChunk));
    }
  };

  await ChatQnAService.postPromptForStreamedResponse(
    prompt,
    promptRequestParams,
    abortSignal,
    onMessageHandler,
  );
};

export const handleBufferedResponse = async (
  prompt: string,
  promptRequestParams: PromptRequestParams,
  abortSignal: AbortSignal,
  dispatch: (action: PayloadAction<string>) => void,
) => {
  const text = await ChatQnAService.postPromptForBufferedResponse(
    prompt,
    promptRequestParams,
    abortSignal,
  );
  dispatch(updateBotMessageText(text));
};
