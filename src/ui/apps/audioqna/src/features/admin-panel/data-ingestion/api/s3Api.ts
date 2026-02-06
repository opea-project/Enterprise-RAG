// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import { PostFileRequest } from "@/features/admin-panel/data-ingestion/types/api";
import { RootState } from "@/store";
import { handleOnQueryStarted, transformErrorMessage } from "@/utils/api";
import { keycloakService } from "@/utils/auth";

const s3ApiBaseQuery = fetchBaseQuery({
  prepareHeaders: (headers) => {
    const token = keycloakService.getToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return headers;
  },
});

export const s3Api = createApi({
  reducerPath: "s3Api",
  baseQuery: s3ApiBaseQuery,
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

export const { usePostFileMutation, useDeleteFileMutation } = s3Api;

export const selectS3Api = (state: RootState) => state.s3Api;
