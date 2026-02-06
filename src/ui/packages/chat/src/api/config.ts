// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const CHAT_HISTORY_API_ENDPOINTS = {
  GET_CHAT_HISTORY: "/v1/chat_history/get",
  SAVE_CHAT_HISTORY: "/v1/chat_history/save",
  CHANGE_CHAT_HISTORY_NAME: "/v1/chat_history/change_name",
  DELETE_CHAT_HISTORY: "/v1/chat_history/delete",
} as const;

export const ABORT_ERROR_MESSAGE = "User interrupted chatbot response.";
export const CONTENT_TYPE_ERROR_MESSAGE =
  "Response from chat cannot be processed - Unsupported Content-Type";
export const DEFAULT_ERROR_MESSAGE =
  "An error occurred. Please contact your administrator for further details.";

export const HTTP_ERRORS = {
  REQUEST_TIMEOUT: {
    statusCode: 408,
    errorMessage:
      "Your request took too long to complete. Please try again later or contact your administrator if the problem persists.",
  },
  PAYLOAD_TOO_LARGE: {
    statusCode: 413,
    errorMessage:
      "Your prompt seems to be too large to be processed. Please shorten your prompt and send it again.",
  },
  TOO_MANY_REQUESTS: {
    statusCode: 429,
    errorMessage:
      "You've reached the limit of requests. Please take a short break and try again soon.",
  },
  GUARDRAILS_ERROR: {
    statusCode: 466,
    parsingErrorMessages: {
      INVALID_FORMAT:
        "Cannot extract guardrails response error: Invalid response format",
      MISSING_ERROR:
        "Cannot extract guardrails response error: Missing error data in response",
      INVALID_ERROR_FORMAT:
        "Cannot extract guardrails response error: Invalid response data error format",
      UNKNOWN: "Unknown guardrails error",
      PARSING_FAILED: "Error parsing guardrails response",
    },
  },
  CLIENT_CLOSED_REQUEST: {
    statusCode: 499,
    errorMessage: ABORT_ERROR_MESSAGE,
  },
} as const;
