// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { KeycloakService } from "@intel-enterprise-rag-ui/auth";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { CHAT_HISTORY_API_ENDPOINTS } from "@/api/config";
import {
  ApiChatItemData,
  ChangeChatNameRequest,
  DeleteChatRequest,
  GetAllChatsResponse,
  GetChatByIdRequest,
  GetChatByIdResponse,
  SaveChatRequest,
  SaveChatResponse,
} from "@/types/api";

const CHATS_LIST_TAG = "Chats List";
const CHAT_ITEM_TAG = "Chat Item";

export const createChatHistoryApi = (keycloakService: KeycloakService) =>
  createApi({
    reducerPath: "chatHistoryApi",
    baseQuery: fetchBaseQuery({
      prepareHeaders: async (headers: Headers) => {
        await keycloakService.refreshToken();
        headers.set("Authorization", `Bearer ${keycloakService.getToken()}`);
        return headers;
      },
    }),
    tagTypes: [CHATS_LIST_TAG, CHAT_ITEM_TAG],
    endpoints: (builder) => ({
      getAllChats: builder.query<GetAllChatsResponse, void>({
        query: () => ({
          url: CHAT_HISTORY_API_ENDPOINTS.GET_CHAT_HISTORY,
        }),
        transformResponse: (response: ApiChatItemData[]) =>
          response.map(({ id, history_name }) => ({
            id: id,
            name: history_name,
          })),
        providesTags: [CHATS_LIST_TAG],
      }),
      getChatById: builder.query<GetChatByIdResponse, GetChatByIdRequest>({
        query: ({ id }) => ({
          url: CHAT_HISTORY_API_ENDPOINTS.GET_CHAT_HISTORY,
          params: { history_id: id },
        }),
        providesTags: (result, _, { id }) =>
          result ? [{ type: CHAT_ITEM_TAG, id }] : [],
      }),
      saveChat: builder.mutation<SaveChatResponse, SaveChatRequest>({
        query: ({ history, id }) => ({
          url: CHAT_HISTORY_API_ENDPOINTS.SAVE_CHAT_HISTORY,
          method: "POST",
          body: { history, id },
        }),
        transformResponse: ({ id, history_name }: ApiChatItemData) => ({
          id,
          name: history_name,
        }),
        invalidatesTags: () => [CHATS_LIST_TAG],
      }),
      changeChatName: builder.mutation<void, ChangeChatNameRequest>({
        query: ({ id, newName }) => ({
          url: CHAT_HISTORY_API_ENDPOINTS.CHANGE_CHAT_HISTORY_NAME,
          method: "POST",
          body: { id, history_name: newName },
        }),
        invalidatesTags: (_, __, { id }) => [
          { type: CHAT_ITEM_TAG, id },
          CHATS_LIST_TAG,
        ],
      }),
      deleteChat: builder.mutation<void, DeleteChatRequest>({
        query: ({ id }) => ({
          url: CHAT_HISTORY_API_ENDPOINTS.DELETE_CHAT_HISTORY,
          method: "DELETE",
          params: { history_id: id },
        }),
        invalidatesTags: [CHATS_LIST_TAG],
      }),
    }),
  });

type ChatHistoryApi = ReturnType<typeof createChatHistoryApi>;
export type UseGetAllChatsQuery =
  ChatHistoryApi["endpoints"]["getAllChats"]["useQuery"];
export type UseLazyGetChatByIdQuery =
  ChatHistoryApi["endpoints"]["getChatById"]["useLazyQuery"];
export type UseLazyGetAllChatsQuery =
  ChatHistoryApi["endpoints"]["getAllChats"]["useLazyQuery"];
export type UseSaveChatMutation =
  ChatHistoryApi["endpoints"]["saveChat"]["useMutation"];
export type UseDeleteChatMutation =
  ChatHistoryApi["endpoints"]["deleteChat"]["useMutation"];
export type UseChangeChatNameMutation =
  ChatHistoryApi["endpoints"]["changeChatName"]["useMutation"];
