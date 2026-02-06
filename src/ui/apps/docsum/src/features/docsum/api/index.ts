// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import {
  DOCSUM_API_ENDPOINTS,
  ERROR_MESSAGES,
} from "@/features/docsum/api/config";
import {
  SummarizeFileRequest,
  SummarizePlainTextRequest,
  SummarizeResponse,
} from "@/features/docsum/api/types";
import { handleSummaryStreamResponse } from "@/features/docsum/utils/api";
import { getErrorMessage } from "@/utils/api";
import { keycloakService } from "@/utils/auth";

export const summarizationApi = createApi({
  reducerPath: "summarizationApi",
  baseQuery: fetchBaseQuery({
    baseUrl: DOCSUM_API_ENDPOINTS.BASE_URL,
    prepareHeaders: async (headers: Headers) => {
      await keycloakService.refreshToken();
      headers.set("Authorization", `Bearer ${keycloakService.getToken()}`);
      headers.set("Content-Type", "application/json");
      return headers;
    },
  }),
  endpoints: (builder) => ({
    summarizePlainText: builder.mutation<
      SummarizeResponse,
      SummarizePlainTextRequest
    >({
      query: ({ text, summaryType, onSummaryUpdate }) => ({
        url: "",
        method: "POST",
        body: {
          texts: [text],
          ...(summaryType && { summary_type: summaryType }),
        },
        responseHandler: async (response) => {
          if (!response.ok) {
            return Promise.reject(response);
          }

          await handleSummaryStreamResponse(response, onSummaryUpdate);
        },
      }),
      transformErrorResponse: (error) =>
        getErrorMessage(error, ERROR_MESSAGES.SUMMARIZE_TEXT),
    }),
    summarizeFile: builder.mutation<SummarizeResponse, SummarizeFileRequest>({
      query: ({ fileData, summaryType, onSummaryUpdate }) => ({
        url: "",
        method: "POST",
        body: {
          files: [fileData],
          ...(summaryType && { summary_type: summaryType }),
        },
        responseHandler: async (response) => {
          if (!response.ok) {
            return Promise.reject(response);
          }

          await handleSummaryStreamResponse(response, onSummaryUpdate);
        },
      }),
      transformErrorResponse: (error) =>
        getErrorMessage(error, ERROR_MESSAGES.SUMMARIZE_FILE),
    }),
  }),
});

export const { useSummarizePlainTextMutation, useSummarizeFileMutation } =
  summarizationApi;
