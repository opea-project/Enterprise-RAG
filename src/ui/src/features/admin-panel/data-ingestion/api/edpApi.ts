// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

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
  GetFilePresignedUrlRequest,
  GetS3BucketsListResponseData,
  PostFileToExtractTextRequest,
} from "@/features/admin-panel/data-ingestion/types/api";
import { handleOnQueryStarted } from "@/features/admin-panel/data-ingestion/utils/api";
import { getToken, refreshToken } from "@/lib/auth";
import { constructUrlWithUuid } from "@/utils";
import { onRefreshTokenFailed, transformErrorMessage } from "@/utils/api";

const edpBaseQuery = fetchBaseQuery({
  baseUrl: API_ENDPOINTS.BASE_URL,
  prepareHeaders: async (headers) => {
    await refreshToken(onRefreshTokenFailed);
    headers.set("Authorization", `Bearer ${getToken()}`);
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
    retryFileAction: builder.mutation({
      query: (uuid) => ({
        url: constructUrlWithUuid(API_ENDPOINTS.RETRY_FILE_ACTION, uuid),
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
  useGetFilePresignedUrlMutation,
  useRetryFileActionMutation,
  usePostFileToExtractTextMutation,
  usePostLinkToExtractTextMutation,
  useGetLinksQuery,
  useLazyGetLinksQuery,
  usePostLinksMutation,
  useRetryLinkActionMutation,
  useDeleteLinkMutation,
  useGetS3BucketsListQuery,
  useLazyGetS3BucketsListQuery,
} = edpApi;
