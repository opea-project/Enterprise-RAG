// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Dispatch, UnknownAction } from "@reduxjs/toolkit";

import {
  UseChangeChatNameMutation,
  UseDeleteChatMutation,
  UseLazyGetAllChatsQuery,
  UseLazyGetChatByIdQuery,
} from "@/api/chatHistory.api";
import { ChatHistoryItemData } from "@/types";

export interface UseChatHistoryHandlersConfig {
  chatHistoryData?: ChatHistoryItemData[];
  useDeleteChatMutation: UseDeleteChatMutation;
  useLazyGetAllChatsQuery: UseLazyGetAllChatsQuery;
  useLazyGetChatByIdQuery: UseLazyGetChatByIdQuery;
  useChangeChatNameMutation: UseChangeChatNameMutation;
  dispatch: Dispatch<UnknownAction>;
  location: { pathname: string };
  navigate: (path: string) => void;
  chatBasePath: string;
  onDeleteError?: (error: { message: string }) => void;
  onRenameError?: (error: { message: string }) => void;
  onExportSuccess?: (blob: Blob, fileName: string) => void;
}

export const useChatHistoryHandlers = (
  config: UseChatHistoryHandlersConfig,
) => {
  const {
    chatHistoryData,
    useDeleteChatMutation,
    useLazyGetAllChatsQuery,
    useLazyGetChatByIdQuery,
    useChangeChatNameMutation,
    location,
    navigate,
    chatBasePath,
    onDeleteError,
    onRenameError,
    onExportSuccess,
  } = config;

  const [deleteChat] = useDeleteChatMutation();
  const [getAllChats] = useLazyGetAllChatsQuery();
  const [getChatById] = useLazyGetChatByIdQuery();
  const [changeChatName] = useChangeChatNameMutation();

  const handleItemPress = (id: string) => {
    navigate(`${chatBasePath}/${id}`);
  };

  const isItemActive = (id: string) => {
    return location.pathname === `${chatBasePath}/${id}`;
  };

  const handleDelete = (chatId: string) => {
    deleteChat({ id: chatId })
      .unwrap()
      .catch((error) => {
        onDeleteError?.(error);
      })
      .then(() => {
        getAllChats();
        if (location.pathname === `${chatBasePath}/${chatId}`) {
          navigate(chatBasePath);
        }
      });
  };

  const handleExport = (chatId: string) => {
    const chatItem = chatHistoryData?.find((item) => item.id === chatId);
    if (!chatItem) return;

    getChatById({ id: chatId })
      .unwrap()
      .then((response) => {
        if (response.history) {
          const itemBlob = new Blob(
            [JSON.stringify(response.history, null, 2)],
            {
              type: "application/json",
            },
          );
          onExportSuccess?.(itemBlob, chatItem.name + ".json");
        }
      });
  };

  const handleRename = (chatId: string, newName: string) => {
    changeChatName({ id: chatId, newName })
      .unwrap()
      .catch((error) => {
        onRenameError?.(error);
      });
  };

  return {
    handleItemPress,
    isItemActive,
    handleDelete,
    handleExport,
    handleRename,
  };
};
