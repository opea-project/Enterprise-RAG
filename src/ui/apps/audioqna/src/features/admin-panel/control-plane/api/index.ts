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
  resetAudioQnAGraph,
  setAudioQnAGraphIsLoading,
  setAudioQnAGraphIsRenderable,
  setupAudioQnAGraph,
} from "@/features/admin-panel/control-plane/store/audioQnAGraph.slice";
import { GetServicesDataResponse } from "@/features/admin-panel/control-plane/types/api";
import { NamespaceStatus } from "@/features/admin-panel/control-plane/types/api/namespaceStatus";
import { parseServiceDetailsResponseData } from "@/features/admin-panel/control-plane/utils/api";
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
        const [audioStatusResult, chatqaStatusResult] = await Promise.all([
          fetchWithBQ({
            url: API_ENDPOINTS.GET_STATUS_AUDIO,
            headers: {
              Authorization: keycloakService.getToken(),
            },
          }),
          fetchWithBQ({
            url: API_ENDPOINTS.GET_STATUS_CHATQA,
            headers: {
              Authorization: keycloakService.getToken(),
            },
          }),
        ]);

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

        const details = parseServiceDetailsResponseData(mergedResponse);

        return { data: { details } };
      },
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        dispatch(resetAudioQnAGraph());

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
          dispatch(setAudioQnAGraphIsLoading(false));
        }
      },
      providesTags: ["Services Data"],
    }),
  }),
});

export const { useGetServicesDataQuery } = controlPlaneApi;
