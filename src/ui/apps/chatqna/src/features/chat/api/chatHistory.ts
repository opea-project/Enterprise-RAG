// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { CHAT_HISTORY_API_ENDPOINTS } from "@/features/chat/config/api";
import {
  APIChatItemData,
  ChangeChatNameRequest,
  DeleteChatRequest,
  GetAllChatsResponse,
  GetChatByIdRequest,
  GetChatByIdResponse,
  SaveChatRequest,
  SaveChatResponse,
} from "@/features/chat/types/api";
import { keycloakService } from "@/utils/auth";

const CHATS_LIST_TAG = "Chats List";
const CHAT_ITEM_TAG = "Chat Item";

export const chatHistoryApi = createApi({
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
      transformResponse: (response: APIChatItemData[]) =>
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
      transformResponse: ({ id, history_name }: APIChatItemData) => ({
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

export const {
  useGetAllChatsQuery,
  useLazyGetAllChatsQuery,
  useGetChatByIdQuery,
  useLazyGetChatByIdQuery,
  useSaveChatMutation,
  useChangeChatNameMutation,
  useDeleteChatMutation,
} = chatHistoryApi;
