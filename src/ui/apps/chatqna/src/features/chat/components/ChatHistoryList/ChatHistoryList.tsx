// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatHistoryList.scss";

import {
  LoadingFallback,
  SearchBar,
} from "@intel-enterprise-rag-ui/components";
import classNames from "classnames";
import { useMemo, useState } from "react";

import { useGetAllChatsQuery } from "@/features/chat/api/chatHistory";
import ChatHistoryItem from "@/features/chat/components/ChatHistoryItem/ChatHistoryItem";
import { ChatItemData } from "@/features/chat/types/api";
import { usePinnedChats } from "@/features/chat/utils/pinnedChats";

const ChatHistoryList = () => {
  const { data, isLoading } = useGetAllChatsQuery();
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
    const pinned: ChatItemData[] = [];
    const unpinned: ChatItemData[] = [];

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

export default ChatHistoryList;
