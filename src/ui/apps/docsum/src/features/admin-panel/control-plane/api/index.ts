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
  resetDocSumGraph,
  setDocSumGraphIsLoading,
  setDocSumGraphIsRenderable,
  setupDocSumGraph,
} from "@/features/admin-panel/control-plane/store/docSumGraph.slice";
import {
  GetServicesDataResponse,
  GetServicesDetailsResponse,
} from "@/features/admin-panel/control-plane/types/api";
import { parseServiceDetailsResponseData } from "@/features/admin-panel/control-plane/utils/api";
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
        const getServicesDetails = await fetchWithBQ({
          url: API_ENDPOINTS.GET_SERVICES_DETAILS,
          headers: {
            Authorization: keycloakService.getToken(),
          },
        });

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

        return { data: { details }, error: undefined };
      },
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        dispatch(resetDocSumGraph());
        try {
          const { data } = await queryFulfilled;
          dispatch(setupDocSumGraph(data));
        } catch (error) {
          const errorMessage = getErrorMessage(
            (error as { error: FetchBaseQueryError }).error,
            ERROR_MESSAGES.GET_SERVICES_DATA,
          );
          dispatch(addNotification({ severity: "error", text: errorMessage }));
          dispatch(setDocSumGraphIsRenderable(false));
        } finally {
          dispatch(setDocSumGraphIsLoading(false));
        }
      },
      providesTags: ["Services Data"],
    }),
  }),
});

export const { useGetServicesDataQuery } = controlPlaneApi;
