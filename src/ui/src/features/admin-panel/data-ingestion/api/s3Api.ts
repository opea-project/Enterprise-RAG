// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import {
  DownloadFileRequest,
  PostFileRequest,
} from "@/features/admin-panel/data-ingestion/types/api";
import { handleOnQueryStarted } from "@/features/admin-panel/data-ingestion/utils/api";
import { RootState } from "@/store";
import { transformErrorMessage } from "@/utils/api";

export const s3Api = createApi({
  reducerPath: "s3Api",
  baseQuery: fetchBaseQuery(),
  endpoints: (builder) => ({
    postFile: builder.mutation<void, PostFileRequest>({
      query: ({ url, file }) => ({
        url,
        method: "PUT",
        body: file,
        headers: {
          "Content-Type": file.type,
        },
      }),
      transformErrorResponse: (error, _, { file }) =>
        transformErrorMessage(
          error,
          `${ERROR_MESSAGES.POST_FILE} ${file.name}`,
        ),
      onQueryStarted: async ({ file }, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          `${ERROR_MESSAGES.POST_FILE} ${file.name}`,
        );
      },
    }),
    downloadFile: builder.query<void, DownloadFileRequest>({
      query: ({ presignedUrl, fileName }) => ({
        url: presignedUrl,
        responseHandler: async (response) => {
          const fileBlob = await response.blob();

          const url = window.URL.createObjectURL(fileBlob);
          const a = document.createElement("a");
          a.href = url;
          a.download = fileName;
          a.click();
          a.remove();
          window.URL.revokeObjectURL(url);
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
    deleteFile: builder.mutation({
      query: (url: string) => ({
        url,
        method: "DELETE",
      }),
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.DELETE_FILE),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.DELETE_FILE,
        );
      },
    }),
  }),
});

export const {
  usePostFileMutation,
  useLazyDownloadFileQuery,
  useDeleteFileMutation,
} = s3Api;

export const selectS3Api = (state: RootState) => state.s3Api;
