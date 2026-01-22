// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FetchBaseQueryError } from "@reduxjs/toolkit/query/react";
import { SerializedError } from "@reduxjs/toolkit/react";

import {
  ABORT_ERROR_MESSAGE,
  DEFAULT_ERROR_MESSAGE,
  HTTP_ERRORS,
} from "@/features/chat/config/api";
import {
  AnswerUpdateHandler,
  ChatErrorResponse,
  SourcesUpdateHandler,
} from "@/features/chat/types/api";

export const handleChatJsonResponse = async (
  response: Response,
  onAnswerUpdate: AnswerUpdateHandler,
  onSourcesUpdate: SourcesUpdateHandler,
) => {
  const json = await response.json();
  onAnswerUpdate(json.text);
  onSourcesUpdate(json.json.reranked_docs || []);
};

export const handleChatStreamResponse = async (
  response: Response,
  onAnswerUpdate: AnswerUpdateHandler,
  onSourcesUpdate: SourcesUpdateHandler,
) => {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder("utf-8");

  let done = false;
  do {
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
        const dataContent = event.slice(5).trim();
        try {
          // Parse OpenAI-style streaming JSON format
          const chunkData = JSON.parse(dataContent);

          if (chunkData.choices && chunkData.choices[0]?.delta?.content) {
            const newTextChunk = chunkData.choices[0].delta.content;
            onAnswerUpdate(newTextChunk);
          }
        } catch (error) {
          // Fallback: treat as plain text if JSON parsing fails
          let newTextChunk = dataContent;
          let quoteRegex = /(?<!\\)'/g;
          if (newTextChunk.startsWith('"')) {
            quoteRegex = /"/g;
          }
          newTextChunk = newTextChunk
            .replace(quoteRegex, "")
            .replace(/\\t/g, "  \t")
            .replace(/\\n/g, "  \n");

          onAnswerUpdate(newTextChunk);
        }
      }

      // handling JSON data event for reranked documents aka sources
      if (event.startsWith("json:")) {
        const jsonText = event.slice(5).trim();
        try {
          const sourcesDataObject = JSON.parse(jsonText);
          const rerankedDocs = sourcesDataObject.reranked_docs || [];
          onSourcesUpdate(rerankedDocs);
        } catch (error) {
          console.error("Error parsing JSON data:", error);
          onSourcesUpdate([]);
        }
      }
    }
  } while (!done);
};

export const createGuardrailsErrorResponse = async (response: Response) => {
  const errorData = await response.json();
  const guardrailsErrorResponse = {} as ChatErrorResponse;
  guardrailsErrorResponse.data = errorData;
  return guardrailsErrorResponse;
};

export const transformChatErrorResponse = (
  error: FetchBaseQueryError,
): Pick<ChatErrorResponse, "status" | "data"> => {
  const responseError = error as ChatErrorResponse;

  if (isAbortResponseError(responseError)) {
    return {
      status: HTTP_ERRORS.CLIENT_CLOSED_REQUEST.statusCode,
      data: HTTP_ERRORS.CLIENT_CLOSED_REQUEST.errorMessage,
    };
  }

  const statusCode = responseError.originalStatus || responseError.status;

  switch (statusCode) {
    case HTTP_ERRORS.REQUEST_TIMEOUT.statusCode:
      return {
        status: HTTP_ERRORS.REQUEST_TIMEOUT.statusCode,
        data: HTTP_ERRORS.REQUEST_TIMEOUT.errorMessage,
      };
    case HTTP_ERRORS.PAYLOAD_TOO_LARGE.statusCode:
      return {
        status: HTTP_ERRORS.PAYLOAD_TOO_LARGE.statusCode,
        data: HTTP_ERRORS.PAYLOAD_TOO_LARGE.errorMessage,
      };
    case HTTP_ERRORS.TOO_MANY_REQUESTS.statusCode:
      return {
        status: HTTP_ERRORS.TOO_MANY_REQUESTS.statusCode,
        data: HTTP_ERRORS.TOO_MANY_REQUESTS.errorMessage,
      };
    case HTTP_ERRORS.GUARDRAILS_ERROR.statusCode:
      return {
        status: HTTP_ERRORS.GUARDRAILS_ERROR.statusCode,
        data: parseGuardrailsResponseErrorDetail(responseError),
      };
    default:
      return {
        status: statusCode,
        data: DEFAULT_ERROR_MESSAGE,
      };
  }
};

const isAbortResponseError = (errorResponse: ChatErrorResponse) => {
  const isFetchAbortError =
    errorResponse.status === "FETCH_ERROR" &&
    errorResponse.error === ABORT_ERROR_MESSAGE;
  const containsBrowserAbortMessage =
    typeof errorResponse.error === "string" &&
    (errorResponse.error.toLowerCase().includes("abort") ||
      errorResponse.error.toLowerCase().includes("interrupt") ||
      errorResponse.error === "AbortError: BodyStreamBuffer was aborted" || // Edge & Chrome
      errorResponse.error === "User interrupted chatbot response."); // Firefox
  const isParsingAbortError =
    errorResponse.status === "PARSING_ERROR" &&
    errorResponse.originalStatus === 200 &&
    containsBrowserAbortMessage;
  return isFetchAbortError || isParsingAbortError;
};

const parseGuardrailsResponseErrorDetail = (
  responseError: ChatErrorResponse,
) => {
  try {
    if (!isChatErrorResponseDataString(responseError.data)) {
      return HTTP_ERRORS.GUARDRAILS_ERROR.parsingErrorMessages.INVALID_FORMAT;
    }

    const parsedResponseData = JSON.parse(responseError.data);

    if (!parsedResponseData.error) {
      return HTTP_ERRORS.GUARDRAILS_ERROR.parsingErrorMessages.MISSING_ERROR;
    } else if (typeof parsedResponseData.error !== "string") {
      return HTTP_ERRORS.GUARDRAILS_ERROR.parsingErrorMessages
        .INVALID_ERROR_FORMAT;
    }

    const errorObj = JSON.parse(parsedResponseData.error);
    return (
      errorObj.detail ||
      HTTP_ERRORS.GUARDRAILS_ERROR.parsingErrorMessages.UNKNOWN
    );
  } catch {
    return HTTP_ERRORS.GUARDRAILS_ERROR.parsingErrorMessages.PARSING_FAILED;
  }
};

export const isChatErrorResponse = (
  error: FetchBaseQueryError | SerializedError | undefined,
): error is ChatErrorResponse =>
  error !== null &&
  typeof error === "object" &&
  "status" in error &&
  "data" in error;

export const isChatErrorResponseDataString = (data: unknown): data is string =>
  typeof data === "string";
