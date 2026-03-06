// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { addNotification } from "@intel-enterprise-rag-ui/components";
import {
  API_ENDPOINTS,
  ChangeArgumentsRequest,
  ERROR_MESSAGES,
  GetServicesDataResponse,
  GetServicesParametersResponse,
  NamespaceStatus,
  parseServiceDetails,
  parseServicesParameters,
  PostRetrieverQueryRequest,
} from "@intel-enterprise-rag-ui/control-plane";
import {
  createApi,
  fetchBaseQuery,
  FetchBaseQueryError,
} from "@reduxjs/toolkit/query/react";

import {
  resetAudioQnAGraph,
  setAudioQnAGraphIsLoading,
  setAudioQnAGraphIsRenderable,
  setupAudioQnAGraph,
} from "@/features/admin-panel/control-plane/store/audioQnAGraph.slice";
import {
  SERVICE_NAME_NODE_ID_MAP,
  SERVICE_NODE_IDS,
} from "@/features/admin-panel/control-plane/utils/api";
import {
  getErrorMessage,
  mergeNamespaceStatuses,
  transformErrorMessage,
} from "@/utils/api";
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
        const [getServicesParameters, audioStatusResult, chatqaStatusResult] =
          await Promise.all([
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
              url: API_ENDPOINTS.GET_AUDIO_STATUS,
              headers: {
                Authorization: keycloakService.getToken(),
              },
            }),
            fetchWithBQ({
              url: API_ENDPOINTS.GET_CHATQNA_STATUS,
              headers: {
                Authorization: keycloakService.getToken(),
              },
            }),
          ]);

        if (
          getServicesParameters.error &&
          audioStatusResult.error &&
          chatqaStatusResult.error
        ) {
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

        if (audioStatusResult.error || chatqaStatusResult.error) {
          const error = transformErrorMessage(
            (audioStatusResult.error ||
              chatqaStatusResult.error) as FetchBaseQueryError,
            ERROR_MESSAGES.GET_STATUS,
          );
          return { error };
        }

        const mergedResponse = mergeNamespaceStatuses(
          audioStatusResult.data as NamespaceStatus,
          chatqaStatusResult.data as NamespaceStatus,
        );

        const details = parseServiceDetails(mergedResponse, {
          serviceNameNodeIdMap: SERVICE_NAME_NODE_ID_MAP,
          serviceNodeIds: SERVICE_NODE_IDS,
        });

        const parameters = parseServicesParameters(
          (getServicesParameters.data as GetServicesParametersResponse)
            .parameters,
        );

        return { data: { details, parameters }, error: undefined };
      },
      onQueryStarted: async (
        _,
        { dispatch, queryFulfilled, getCacheEntry },
      ) => {
        const cacheEntry = getCacheEntry();
        const isInitialLoad = !cacheEntry?.data;

        if (isInitialLoad) {
          dispatch(resetAudioQnAGraph());
        }

        try {
          const { data } = await queryFulfilled;
          dispatch(setupAudioQnAGraph(data));
        } catch (error) {
          const errorMessage = getErrorMessage(
            (error as { error: FetchBaseQueryError }).error,
            ERROR_MESSAGES.GET_STATUS,
          );
          dispatch(addNotification({ severity: "error", text: errorMessage }));
          dispatch(setAudioQnAGraphIsRenderable(false));
        } finally {
          if (isInitialLoad) {
            dispatch(setAudioQnAGraphIsLoading(false));
          }
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
        dispatch(resetAudioQnAGraph());

        try {
          await queryFulfilled;
        } catch (error) {
          const errorMessage = getErrorMessage(
            (error as { error: FetchBaseQueryError }).error,
            ERROR_MESSAGES.CHANGE_ARGUMENTS,
          );
          dispatch(addNotification({ severity: "error", text: errorMessage }));
        } finally {
          dispatch(setAudioQnAGraphIsLoading(false));
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
  useLazyGetServicesDataQuery,
  useChangeArgumentsMutation,
  usePostRetrieverQueryMutation,
} = controlPlaneApi;
