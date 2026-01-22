// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { addNotification } from "@intel-enterprise-rag-ui/components";
import {
  createApi,
  fetchBaseQuery,
  FetchBaseQueryError,
} from "@reduxjs/toolkit/query/react";

import {
  API_ENDPOINTS,
  ERROR_MESSAGES,
} from "@/features/admin-panel/control-plane/config/api";
import {
  resetChatQnAGraph,
  setChatQnAGraphIsLoading,
  setChatQnAGraphIsRenderable,
  setupChatQnAGraph,
} from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import {
  ChangeArgumentsRequest,
  GetServicesDataResponse,
  GetServicesDetailsResponse,
  GetServicesParametersResponse,
  PostRetrieverQueryRequest,
} from "@/features/admin-panel/control-plane/types/api";
import {
  parseServiceDetailsResponseData,
  parseServicesParameters,
} from "@/features/admin-panel/control-plane/utils/api";
import { getErrorMessage, transformErrorMessage } from "@/utils/api";
import { keycloakService } from "@/utils/auth";

const controlPlaneBaseQuery = fetchBaseQuery({
  prepareHeaders: async (headers) => {
    await keycloakService.refreshToken();
    return headers;
  },
});

export const controlPlaneApi = createApi({
  reducerPath: "controlPlaneApi",
  baseQuery: controlPlaneBaseQuery,
  tagTypes: ["Services Data"],
  endpoints: (builder) => ({
    getServicesData: builder.query<GetServicesDataResponse, void>({
      queryFn: async (_arg, _queryApi, _extraOptions, fetchWithBQ) => {
        const [getServicesParameters, getServicesDetails] = await Promise.all([
          fetchWithBQ({
            url: API_ENDPOINTS.GET_SERVICES_PARAMETERS,
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${keycloakService.getToken()}`,
            },
            body: JSON.stringify({ text: "" }),
          }),
          fetchWithBQ({
            url: API_ENDPOINTS.GET_SERVICES_DETAILS,
            headers: {
              Authorization: keycloakService.getToken(),
            },
          }),
        ]);

        if (getServicesParameters.error && getServicesDetails.error) {
          return {
            error: {
              status: "CUSTOM_ERROR" as const,
              error: ERROR_MESSAGES.GET_SERVICES_DATA,
            },
          };
        }

        if (getServicesParameters.error) {
          const error = transformErrorMessage(
            getServicesParameters.error as FetchBaseQueryError,
            ERROR_MESSAGES.GET_SERVICES_PARAMETERS,
          );
          return { error };
        }

        if (getServicesDetails.error) {
          const error = transformErrorMessage(
            getServicesDetails.error as FetchBaseQueryError,
            ERROR_MESSAGES.GET_SERVICES_DETAILS,
          );
          return { error };
        }

        const details = parseServiceDetailsResponseData(
          getServicesDetails.data as GetServicesDetailsResponse,
        );

        const parameters = parseServicesParameters(
          (getServicesParameters.data as GetServicesParametersResponse)
            .parameters,
        );

        return { data: { details, parameters }, error: undefined };
      },
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        dispatch(resetChatQnAGraph());

        try {
          const { data } = await queryFulfilled;
          dispatch(setupChatQnAGraph(data));
        } catch (error) {
          const errorMessage = getErrorMessage(
            (error as { error: FetchBaseQueryError }).error,
            ERROR_MESSAGES.GET_SERVICES_DATA,
          );
          dispatch(addNotification({ severity: "error", text: errorMessage }));
          dispatch(setChatQnAGraphIsRenderable(false));
        } finally {
          dispatch(setChatQnAGraphIsLoading(false));
        }
      },
      providesTags: ["Services Data"],
    }),
    changeArguments: builder.mutation<Response, ChangeArgumentsRequest>({
      query: (requestBody) => ({
        url: API_ENDPOINTS.CHANGE_ARGUMENTS,
        method: "POST",
        body: JSON.stringify(requestBody),
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${keycloakService.getToken()}`,
        },
      }),
      onQueryStarted: async (_arg, { dispatch, queryFulfilled }) => {
        dispatch(resetChatQnAGraph());

        try {
          await queryFulfilled;
        } catch (error) {
          const errorMessage = getErrorMessage(
            (error as { error: FetchBaseQueryError }).error,
            ERROR_MESSAGES.CHANGE_ARGUMENTS,
          );
          dispatch(addNotification({ severity: "error", text: errorMessage }));
        }
      },
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.CHANGE_ARGUMENTS),
      invalidatesTags: ["Services Data"],
    }),
    postRetrieverQuery: builder.mutation<string, PostRetrieverQueryRequest>({
      query: (requestBody) => ({
        url: API_ENDPOINTS.POST_RETRIEVER_QUERY,
        method: "POST",
        body: JSON.stringify(requestBody),
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${keycloakService.getToken()}`,
        },
        responseHandler: async (response) => await response.text(),
      }),
      transformErrorResponse: (error) =>
        transformErrorMessage(error, ERROR_MESSAGES.POST_RETRIEVER_QUERY),
    }),
  }),
});

export const {
  useGetServicesDataQuery,
  useChangeArgumentsMutation,
  usePostRetrieverQueryMutation,
} = controlPlaneApi;
