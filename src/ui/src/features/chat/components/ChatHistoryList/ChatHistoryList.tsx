// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatHistoryList.scss";

import classNames from "classnames";

import LoadingFallback from "@/components/ui/LoadingFallback/LoadingFallback";
import { useGetAllChatsQuery } from "@/features/chat/api/chatHistory";
import ChatHistoryItem from "@/features/chat/components/ChatHistoryItem/ChatHistoryItem";

const ChatHistoryList = () => {
  const { data, isLoading } = useGetAllChatsQuery();
  const isChatHistoryEmpty = !Array.isArray(data) || data.length === 0;

  const chatHistoryListClass = classNames("chat-history-list", {
    "chat-history-list--empty": isChatHistoryEmpty,
  });

  return (
    <aside aria-label="Chat History List">
      <h3 className="py-3 pl-4">Chat History</h3>
      <div className={chatHistoryListClass}>
        {isLoading && <LoadingFallback />}
        {!isLoading && isChatHistoryEmpty && (
          <p className="text-xs text-gray-500">No chat history available.</p>
        )}
        {!isLoading &&
          !isChatHistoryEmpty &&
          data.map((item) => <ChatHistoryItem key={item.id} itemData={item} />)}
      </div>
    </aside>
  );
};

export default ChatHistoryList;
