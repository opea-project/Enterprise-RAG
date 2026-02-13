// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { downloadBlob } from "@intel-enterprise-rag-ui/utils";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { API_ENDPOINTS, ERROR_MESSAGES } from "@/config/api";
import { DownloadFileRequest, GetFilePresignedUrlRequest } from "@/types/api";
import { handleOnQueryStarted, transformErrorMessage } from "@/utils/api";
import { keycloakService } from "@/utils/auth";

const AUTHORIZED_ENDPOINTS = ["getFilePresignedUrl", "downloadFile"];

const appBaseQuery = fetchBaseQuery({
  prepareHeaders: async (headers, api) => {
    if (AUTHORIZED_ENDPOINTS.includes(api.endpoint)) {
      await keycloakService.refreshToken();
      headers.set("Authorization", `Bearer ${keycloakService.getToken()}`);
    }
    return headers;
  },
});

export const appApi = createApi({
  reducerPath: "appApi",
  baseQuery: appBaseQuery,
  endpoints: (builder) => ({
    downloadFile: builder.query<void, DownloadFileRequest>({
      query: ({ presignedUrl, fileName }) => ({
        url: presignedUrl,
        responseHandler: async (response) => {
          if (!response.ok) {
            return Promise.reject(ERROR_MESSAGES.DOWNLOAD_FILE);
          }

          const fileBlob = await response.blob();
          downloadBlob(fileBlob, fileName);
        },
      }),
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.DOWNLOAD_FILE),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.DOWNLOAD_FILE,
        );
      },
    }),
    getFilePresignedUrl: builder.mutation<string, GetFilePresignedUrlRequest>({
      query: ({ fileName, method, bucketName }) => ({
        url: API_ENDPOINTS.GET_FILE_PRESIGNED_URL,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          object_name: fileName,
          method,
          bucket_name: bucketName,
        }),
        responseHandler: async (response) => {
          if (!response.ok) {
            return Promise.reject(ERROR_MESSAGES.GET_FILE_PRESIGNED_URL);
          }

          const { url } = await response.json();
          return url;
        },
      }),
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.GET_FILE_PRESIGNED_URL),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.GET_FILE_PRESIGNED_URL,
        );
      },
    }),
  }),
});

export const { useLazyDownloadFileQuery, useGetFilePresignedUrlMutation } =
  appApi;
