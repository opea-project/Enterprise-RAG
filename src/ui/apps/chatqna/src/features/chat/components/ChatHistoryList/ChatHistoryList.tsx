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

const ChatHistoryList = () => {
  const { data, isLoading } = useGetAllChatsQuery();
  const [searchFilter, setSearchFilter] = useState("");

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

  return (
    <aside aria-label="Chat History List">
      <div className="mx-2 px-2 pb-2 pt-1">
        <SearchBar
          value={searchFilter}
          placeholder="Search chat history..."
          onChange={setSearchFilter}
        />
      </div>
      <div className={chatHistoryListClass}>
        {isLoading && <LoadingFallback />}
        {!isLoading && isChatHistoryEmpty && (
          <p className="text-xs text-gray-500">{emptyStateMessage}</p>
        )}
        {!isLoading &&
          !isChatHistoryEmpty &&
          filteredData.map((item) => (
            <ChatHistoryItem key={item.id} itemData={item} />
          ))}
      </div>
    </aside>
  );
};

export default ChatHistoryList;
