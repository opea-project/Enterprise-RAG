// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { keycloakService } from "@/utils/auth";

interface SpeechToTextRequest {
  audio: Blob;
  model?: string;
  language?: string;
  response_format?: string;
}

interface SpeechToTextResponse {
  text: string;
}

export const asrApi = createApi({
  reducerPath: "asrApi",
  baseQuery: fetchBaseQuery({
    baseUrl: "/v1",
    prepareHeaders: async (headers: Headers) => {
      await keycloakService.refreshToken();
      headers.set("Authorization", `Bearer ${keycloakService.getToken()}`);
      return headers;
    },
  }),
  endpoints: (builder) => ({
    speechToText: builder.mutation<SpeechToTextResponse, SpeechToTextRequest>({
      query: ({ audio, model, language, response_format }) => {
        const formData = new FormData();
        formData.append("file", audio, "recording.wav");
        if (model) {
          formData.append("model", model);
        }
        if (language) {
          formData.append("language", language);
        }
        if (response_format) {
          formData.append("response_format", response_format);
        }

        return {
          url: "/audio/transcriptions",
          method: "POST",
          body: formData,
          responseHandler: async (response) => {
            if (!response.ok) {
              const errorText = await response.text();
              return Promise.reject({
                status: response.status,
                data: errorText || "Failed to transcribe audio",
              });
            }
            return await response.json();
          },
        };
      },
    }),
  }),
});

export const { useSpeechToTextMutation } = asrApi;
