// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatHistoryList.scss";

import {
  LoadingFallback,
  SearchBar,
} from "@intel-enterprise-rag-ui/components";
import classNames from "classnames";
import { useMemo, useState } from "react";

import type { OnChatHistoryItemPressHandler } from "@/components/chat-history/ChatHistoryItem/ChatHistoryItem";
import { ChatHistoryItem } from "@/components/chat-history/ChatHistoryItem/ChatHistoryItem";
import type { OnDeleteChatHandler } from "@/components/chat-history/DeleteChatDialog/DeleteChatDialog";
import type { OnExportChatHandler } from "@/components/chat-history/ExportChatDialog/ExportChatDialog";
import type { OnRenameChatHandler } from "@/components/chat-history/RenameChatDialog/RenameChatDialog";
import { usePinnedChats } from "@/hooks/usePinnedChats";
import { ChatHistoryItemData } from "@/types";

export type IsItemActiveHandler = (id: string) => boolean;

interface ChatHistoryListProps {
  data?: ChatHistoryItemData[];
  isLoading: boolean;
  onItemPress: OnChatHistoryItemPressHandler;
  isItemActive: IsItemActiveHandler;
  onDelete: OnDeleteChatHandler;
  onExport: OnExportChatHandler;
  onRename: OnRenameChatHandler;
}

export const ChatHistoryList = ({
  data,
  isLoading,
  onItemPress,
  isItemActive,
  onDelete,
  onExport,
  onRename,
}: ChatHistoryListProps) => {
  const [searchFilter, setSearchFilter] = useState("");
  const { pinnedIds, isPinned, togglePinChat } = usePinnedChats();

  const filteredData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    if (!searchFilter.trim()) return data;

    const lowerSearchFilter = searchFilter.toLowerCase();
    return data.filter((item) =>
      item.name.toLowerCase().includes(lowerSearchFilter),
    );
  }, [data, searchFilter]);

  const isChatHistoryEmpty = filteredData.length === 0;

  const emptyStateMessage = searchFilter.trim()
    ? "No chat history matches your search."
    : "No chat history available.";

  const chatHistoryListClass = classNames("chat-history-list", {
    "chat-history-list--empty": isChatHistoryEmpty,
  });

  const { pinnedChats, unpinnedChats } = useMemo(() => {
    const pinned: ChatHistoryItemData[] = [];
    const unpinned: ChatHistoryItemData[] = [];

    if (!isLoading && filteredData) {
      const dataMap = new Map(filteredData.map((item) => [item.id, item]));

      pinnedIds.forEach((id) => {
        const item = dataMap.get(id);
        if (item) {
          pinned.push(item);
        }
      });

      filteredData.forEach((item) => {
        if (!pinnedIds.includes(item.id)) {
          unpinned.push(item);
        }
      });
    }

    return { pinnedChats: pinned, unpinnedChats: unpinned };
  }, [isLoading, filteredData, pinnedIds]);

  const hasPinnedChats = pinnedChats.length > 0;

  return (
    <aside aria-label="Chat History List">
      <div className="chat-history-list__search-bar">
        <SearchBar
          value={searchFilter}
          placeholder="Search chat history..."
          onChange={setSearchFilter}
        />
      </div>
      <div className={chatHistoryListClass}>
        {isLoading && <LoadingFallback />}
        {!isLoading && isChatHistoryEmpty && (
          <p className="chat-history-list__empty-message">
            {emptyStateMessage}
          </p>
        )}
        {!isLoading && !isChatHistoryEmpty && (
          <>
            {hasPinnedChats && (
              <div className="chat-history-list__section">
                <p className="chat-history-list__section-title">Pinned</p>
                <div className="chat-history-list__items">
                  {pinnedChats.map((item) => (
                    <ChatHistoryItem
                      key={item.id}
                      itemData={item}
                      pinned={isPinned(item.id)}
                      onPinChange={() => togglePinChat(item.id)}
                      isActive={isItemActive(item.id)}
                      onPress={() => onItemPress(item.id)}
                      onDelete={onDelete}
                      onExport={onExport}
                      onRename={onRename}
                    />
                  ))}
                </div>
              </div>
            )}
            {unpinnedChats.length > 0 && (
              <div className="chat-history-list__section">
                <p className="chat-history-list__section-title">Chats</p>
                <div className="chat-history-list__items">
                  {unpinnedChats.map((item) => (
                    <ChatHistoryItem
                      key={item.id}
                      itemData={item}
                      pinned={isPinned(item.id)}
                      onPinChange={() => togglePinChat(item.id)}
                      isActive={isItemActive(item.id)}
                      onPress={() => onItemPress(item.id)}
                      onDelete={onDelete}
                      onExport={onExport}
                      onRename={onRename}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </aside>
  );
};
