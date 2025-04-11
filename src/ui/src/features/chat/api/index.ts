// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import {
  addNewBotMessage,
  addNewUserMessage,
  setPrompt,
  updateBotMessageText,
  updateMessageIsStreamed,
} from "@/features/chat/store/conversationFeed.slice";
import { OnMessageTextUpdateHandler } from "@/features/chat/types/api";
import {
  getChatErrorMessage,
  handleChatJsonResponse,
  handleChatStreamResponse,
  handleUnsuccessfulChatResponse,
  transformChatErrorMessage,
} from "@/features/chat/utils/api";
import { getToken, refreshToken } from "@/lib/auth";
import { onRefreshTokenFailed } from "@/utils/api";

interface PostPromptRequest {
  prompt: string;
  signal: AbortSignal;
  onMessageTextUpdate: OnMessageTextUpdateHandler;
}

export const chatQnAApi = createApi({
  reducerPath: "chatQnAApi",
  baseQuery: fetchBaseQuery({
    prepareHeaders: async (headers: Headers) => {
      await refreshToken(onRefreshTokenFailed);

      headers.set("Authorization", `Bearer ${getToken()}`);
      headers.set("Content-Type", "application/json");

      return headers;
    },
  }),
  endpoints: (builder) => ({
    postPrompt: builder.mutation<void, PostPromptRequest>({
      query: ({ prompt, signal, onMessageTextUpdate }) => ({
        url: "/api/v1/chatqna",
        method: "POST",
        body: JSON.stringify({
          text: prompt,
        }),
        signal,
        responseHandler: async (response) => {
          if (!response.ok) {
            await handleUnsuccessfulChatResponse(response);
          } else {
            const contentType = response.headers.get("Content-Type");
            if (contentType && contentType.includes("application/json")) {
              await handleChatJsonResponse(response, onMessageTextUpdate);
            } else if (
              contentType &&
              contentType.includes("text/event-stream")
            ) {
              await handleChatStreamResponse(response, onMessageTextUpdate);
            } else {
              throw {
                status: response.status,
                data: "Response from chat cannot be processed - Unsupported Content-Type",
              };
            }
          }
        },
      }),
      transformErrorResponse: (error) => transformChatErrorMessage(error),
      onQueryStarted: async ({ prompt }, { queryFulfilled, dispatch }) => {
        try {
          dispatch(addNewUserMessage(prompt));
          dispatch(setPrompt(""));
          dispatch(addNewBotMessage());
          dispatch(updateMessageIsStreamed(true));

          await queryFulfilled;
        } catch (error) {
          const errorMessage = getChatErrorMessage(error);
          dispatch(updateBotMessageText(errorMessage));
        } finally {
          dispatch(updateMessageIsStreamed(false));
        }
      },
    }),
  }),
});

export const { usePostPromptMutation } = chatQnAApi;
