// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import {
  CHATQNA_API_ENDPOINTS,
  CONTENT_TYPE_ERROR_MESSAGE,
  HTTP_ERRORS,
} from "@/features/chat/config/api";
import { PostPromptRequest } from "@/features/chat/types/api";
import {
  createGuardrailsErrorResponse,
  handleChatJsonResponse,
  handleChatStreamResponse,
  transformChatErrorResponse,
} from "@/features/chat/utils/api";
import { keycloakService } from "@/utils/auth";

export const chatQnAApi = createApi({
  reducerPath: "chatQnAApi",
  baseQuery: fetchBaseQuery({
    prepareHeaders: async (headers: Headers) => {
      await keycloakService.refreshToken();

      headers.set("Authorization", `Bearer ${keycloakService.getToken()}`);
      headers.set("Content-Type", "application/json");

      return headers;
    },
  }),
  endpoints: (builder) => ({
    postPrompt: builder.mutation<void, PostPromptRequest>({
      query: ({ prompt, id, signal, onAnswerUpdate, onSourcesUpdate }) => ({
        url: CHATQNA_API_ENDPOINTS.POST_PROMPT,
        method: "POST",
        body: {
          text: prompt,
          history_id: id,
        },
        signal,
        responseHandler: async (response) => {
          if (response.status === HTTP_ERRORS.GUARDRAILS_ERROR.statusCode) {
            const guardrailsErrorResponse =
              await createGuardrailsErrorResponse(response);
            return Promise.reject(guardrailsErrorResponse);
          }

          if (!response.ok) {
            return Promise.reject(response);
          }

          const contentType = response.headers.get("Content-Type");
          if (contentType && contentType.includes("application/json")) {
            await handleChatJsonResponse(
              response,
              onAnswerUpdate,
              onSourcesUpdate,
            );
          } else if (contentType && contentType.includes("text/event-stream")) {
            await handleChatStreamResponse(
              response,
              onAnswerUpdate,
              onSourcesUpdate,
            );
          } else {
            throw {
              status: response.status,
              data: CONTENT_TYPE_ERROR_MESSAGE,
            };
          }
        },
      }),
      transformErrorResponse: (error) => transformChatErrorResponse(error),
    }),
  }),
});

export const { usePostPromptMutation } = chatQnAApi;
