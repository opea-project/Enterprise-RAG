// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatHistoryItem.scss";

import { Anchor, Tooltip } from "@intel-enterprise-rag-ui/components";
import classNames from "classnames";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { paths } from "@/config/paths";
import ChatHistoryItemMenu from "@/features/chat/components/ChatHistoryItemMenu/ChatHistoryItemMenu";
import { ChatItemData } from "@/features/chat/types/api";

const TITLE_OVERFLOW_LIMIT = 19;

interface ChatHistoryItemProps {
  itemData: ChatItemData;
}

const ChatHistoryItem = ({ itemData }: ChatHistoryItemProps) => {
  const { id, name } = itemData;

  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = location.pathname === `${paths.chat}/${id}`;

  const handleEntryPress = () => {
    if (isActive) return;
    navigate(`${paths.chat}/${id}`);
  };

  const className = classNames("chat-history-item", {
    "chat-history-item--active": isActive,
    "chat-history-item--has-menu-open": isMenuOpen,
  });

  let titleElement = <span>{name}</span>;

  if (name.length > TITLE_OVERFLOW_LIMIT) {
    const truncatedTitle = `${name.slice(0, TITLE_OVERFLOW_LIMIT)}...`;
    titleElement = (
      <Tooltip
        title={name}
        trigger={<span>{truncatedTitle}</span>}
        placement="right"
      />
    );
  }

  return (
    <Anchor className={className} onPress={handleEntryPress}>
      {titleElement}
      <ChatHistoryItemMenu
        itemData={itemData}
        isOpen={isMenuOpen}
        onOpenChange={setIsMenuOpen}
      />
    </Anchor>
  );
};

export default ChatHistoryItem;
