// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SideMenu } from "@intel-enterprise-rag-ui/layouts";

import type { OnChatHistoryItemPressHandler } from "@/components/chat-history/ChatHistoryItem/ChatHistoryItem";
import type { IsItemActiveHandler } from "@/components/chat-history/ChatHistoryList/ChatHistoryList";
import { ChatHistoryList } from "@/components/chat-history/ChatHistoryList/ChatHistoryList";
import type { OnDeleteChatHandler } from "@/components/chat-history/DeleteChatDialog/DeleteChatDialog";
import type { OnExportChatHandler } from "@/components/chat-history/ExportChatDialog/ExportChatDialog";
import type { OnRenameChatHandler } from "@/components/chat-history/RenameChatDialog/RenameChatDialog";
import { ChatHistoryItemData } from "@/types";

interface ChatSideMenuProps {
  isOpen: boolean;
  chatHistoryData?: ChatHistoryItemData[];
  isLoadingChatHistory: boolean;
  onItemPress: OnChatHistoryItemPressHandler;
  isItemActive: IsItemActiveHandler;
  onDelete: OnDeleteChatHandler;
  onExport: OnExportChatHandler;
  onRename: OnRenameChatHandler;
}

export const ChatSideMenu = ({
  isOpen,
  chatHistoryData,
  isLoadingChatHistory,
  onItemPress,
  isItemActive,
  onDelete,
  onExport,
  onRename,
}: ChatSideMenuProps) => (
  <SideMenu direction="left" isOpen={isOpen} ariaLabel="Chat Side Menu">
    <ChatHistoryList
      data={chatHistoryData}
      isLoading={isLoadingChatHistory}
      onItemPress={onItemPress}
      isItemActive={isItemActive}
      onDelete={onDelete}
      onExport={onExport}
      onRename={onRename}
    />
  </SideMenu>
);
