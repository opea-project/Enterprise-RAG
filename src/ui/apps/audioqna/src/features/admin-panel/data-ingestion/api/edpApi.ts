// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { constructUrlWithUuid } from "@intel-enterprise-rag-ui/utils";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import {
  API_ENDPOINTS,
  ERROR_MESSAGES,
} from "@/features/admin-panel/data-ingestion/config/api";
import {
  FileDataItem,
  LinkDataItem,
} from "@/features/admin-panel/data-ingestion/types";
import {
  FileSyncDataItem,
  GetS3BucketsListResponseData,
  PostFileToExtractTextRequest,
} from "@/features/admin-panel/data-ingestion/types/api";
import { handleOnQueryStarted, transformErrorMessage } from "@/utils/api";
import { keycloakService } from "@/utils/auth";

const edpBaseQuery = fetchBaseQuery({
  baseUrl: API_ENDPOINTS.BASE_URL,
  prepareHeaders: async (headers) => {
    await keycloakService.refreshToken();
    headers.set("Authorization", `Bearer ${keycloakService.getToken()}`);
    return headers;
  },
});

export const edpApi = createApi({
  reducerPath: "edpApi",
  baseQuery: edpBaseQuery,
  tagTypes: ["Files", "Links"],
  endpoints: (builder) => ({
    getFiles: builder.query<FileDataItem[], void>({
      query: () => API_ENDPOINTS.GET_FILES,
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.GET_FILES),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.GET_FILES,
        );
      },
      providesTags: ["Files"],
    }),

    retryFileAction: builder.mutation({
      query: (uuid) => ({
        url: constructUrlWithUuid(API_ENDPOINTS.RETRY_FILE_ACTION, uuid),
        method: "POST",
      }),
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.RETRY_FILE_ACTION),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.RETRY_FILE_ACTION,
        );
      },
      invalidatesTags: ["Files"],
    }),
    postFileToExtractText: builder.mutation<
      string,
      PostFileToExtractTextRequest
    >({
      query: ({ uuid, queryParams }) => ({
        url: constructUrlWithUuid(
          API_ENDPOINTS.POST_FILE_TO_EXTRACT_TEXT,
          uuid,
        ),
        method: "POST",
        params: queryParams,
      }),
    }),
    postLinkToExtractText: builder.mutation<
      string,
      PostFileToExtractTextRequest
    >({
      query: ({ uuid, queryParams }) => ({
        url: constructUrlWithUuid(
          API_ENDPOINTS.POST_LINK_TO_EXTRACT_TEXT,
          uuid,
        ),
        method: "POST",
        params: queryParams,
      }),
    }),
    getFilesSync: builder.query<FileSyncDataItem[], void>({
      query: () => API_ENDPOINTS.GET_FILES_SYNC,
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.GET_FILES_SYNC),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.GET_FILES_SYNC,
        );
      },
    }),
    postFilesSync: builder.mutation<void, void>({
      query: () => ({
        url: API_ENDPOINTS.POST_FILES_SYNC,
        method: "POST",
      }),
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.POST_FILES_SYNC),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.POST_FILES_SYNC,
        );
      },
    }),
    getLinks: builder.query<LinkDataItem[], void>({
      query: () => API_ENDPOINTS.GET_LINKS,
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.GET_LINKS),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.GET_LINKS,
        );
      },
      providesTags: ["Links"],
    }),
    postLinks: builder.mutation<void, string[]>({
      query: (links) => ({
        url: API_ENDPOINTS.POST_LINKS,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ links }),
      }),
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.POST_LINKS),
      invalidatesTags: ["Links"],
    }),
    retryLinkAction: builder.mutation({
      query: (uuid) => ({
        url: constructUrlWithUuid(API_ENDPOINTS.RETRY_LINK_ACTION, uuid),
        method: "POST",
      }),
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.RETRY_LINK_ACTION),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.RETRY_LINK_ACTION,
        );
      },
      invalidatesTags: ["Links"],
    }),
    deleteLink: builder.mutation({
      query: (uuid) => ({
        url: constructUrlWithUuid(API_ENDPOINTS.DELETE_LINK, uuid),
        method: "DELETE",
      }),
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.DELETE_LINK),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.DELETE_LINK,
        );
      },
      invalidatesTags: ["Links"],
    }),
    getS3BucketsList: builder.query<string[], void>({
      query: () => ({
        url: API_ENDPOINTS.GET_S3_BUCKETS_LIST,
        responseHandler: async (response) => {
          const responseData = await response.json();
          return responseData;
        },
      }),
      transformResponse: (responseData: GetS3BucketsListResponseData) =>
        responseData.buckets ?? [],
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.GET_S3_BUCKETS_LIST),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        await handleOnQueryStarted(
          queryFulfilled,
          dispatch,
          ERROR_MESSAGES.GET_S3_BUCKETS_LIST,
        );
      },
    }),
  }),
});

export const {
  useGetFilesQuery,
  useLazyGetFilesQuery,
  useRetryFileActionMutation,
  usePostFileToExtractTextMutation,
  usePostLinkToExtractTextMutation,
  useGetFilesSyncQuery,
  useLazyGetFilesSyncQuery,
  usePostFilesSyncMutation,
  useGetLinksQuery,
  useLazyGetLinksQuery,
  usePostLinksMutation,
  useRetryLinkActionMutation,
  useDeleteLinkMutation,
  useGetS3BucketsListQuery,
  useLazyGetS3BucketsListQuery,
} = edpApi;
