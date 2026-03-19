// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { validateAudioBlob } from "@/features/chat/utils/api";
import { keycloakService } from "@/utils/auth";

export interface TextToSpeechRequest {
  input: string;
  voice?: string;
  response_format?: string;
  signal?: AbortSignal;
}

export interface TextToSpeechResponse {
  audioUrl: string;
}

export const ttsApi = createApi({
  reducerPath: "ttsApi",
  baseQuery: fetchBaseQuery({
    baseUrl: "/v1",
    prepareHeaders: async (headers: Headers) => {
      await keycloakService.refreshToken();
      headers.set("Authorization", `Bearer ${keycloakService.getToken()}`);
      headers.set("Content-Type", "application/json");
      return headers;
    },
  }),
  keepUnusedDataFor: 0, // prevents caching for audio data
  endpoints: (builder) => ({
    textToSpeech: builder.mutation<TextToSpeechResponse, TextToSpeechRequest>({
      query: ({ input, signal }) => ({
        url: "/audio/speech",
        method: "POST",
        body: { input },
        signal,
        responseHandler: async (response) => {
          if (!response.ok) {
            const errorText = await response.text();
            return Promise.reject({
              status: response.status,
              data: errorText || "Failed to generate speech",
            });
          }

          // Buffer the entire response
          const blob = await response.blob();
          validateAudioBlob(blob);
          const audioUrl = URL.createObjectURL(blob);

          return { audioUrl };
        },
      }),
    }),
  }),
});

export const { useTextToSpeechMutation } = ttsApi;
