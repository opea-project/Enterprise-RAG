// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { addNotification } from "@intel-enterprise-rag-ui/components";
import {
  API_ENDPOINTS,
  ERROR_MESSAGES,
  GetServicesDataResponse,
  GetServicesDetailsResponse,
  parseServiceDetails,
} from "@intel-enterprise-rag-ui/control-plane";
import {
  createApi,
  fetchBaseQuery,
  FetchBaseQueryError,
} from "@reduxjs/toolkit/query/react";

import {
  resetDocSumGraph,
  setDocSumGraphIsLoading,
  setDocSumGraphIsRenderable,
  setupDocSumGraph,
} from "@/features/admin-panel/control-plane/store/docSumGraph.slice";
import {
  SERVICE_NAME_NODE_ID_MAP,
  SERVICE_NODE_IDS,
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
        const getServicesDetails = await fetchWithBQ({
          url: API_ENDPOINTS.GET_DOCSUM_STATUS,
          headers: {
            Authorization: keycloakService.getToken(),
          },
        });

        if (getServicesDetails.error) {
          const error = transformErrorMessage(
            getServicesDetails.error as FetchBaseQueryError,
            ERROR_MESSAGES.GET_STATUS,
          );
          return { error };
        }

        const details = parseServiceDetails(
          getServicesDetails.data as GetServicesDetailsResponse,
          {
            serviceNameNodeIdMap: SERVICE_NAME_NODE_ID_MAP,
            serviceNodeIds: SERVICE_NODE_IDS,
          },
        );

        return { data: { details }, error: undefined };
      },
      onQueryStarted: async (
        _,
        { dispatch, queryFulfilled, getCacheEntry },
      ) => {
        const cacheEntry = getCacheEntry();
        const isInitialLoad = !cacheEntry?.data;

        if (isInitialLoad) {
          dispatch(resetDocSumGraph());
        }

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
          if (isInitialLoad) {
            dispatch(setDocSumGraphIsLoading(false));
          }
        }
      },
      providesTags: ["Services Data"],
    }),
  }),
});

export const { useGetServicesDataQuery, useLazyGetServicesDataQuery } =
  controlPlaneApi;
