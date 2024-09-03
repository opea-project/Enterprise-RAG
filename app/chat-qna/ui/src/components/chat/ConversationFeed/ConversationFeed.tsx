// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ConversationFeed.scss";

import { Typography } from "@mui/material";
import { useEffect } from "react";

import ChatMessage from "@/components/chat/ChatMessage/ChatMessage";
import keycloakService from "@/services/keycloakService";
import { selectMessages } from "@/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";

const conversationFeedId = "chat-conversation-feed";

const ConversationFeed = () => {
  const feedMessages = useAppSelector(selectMessages);

  const scrollDownConversationFeed = () => {
    const conversationFeed = document.getElementById(conversationFeedId);
    if (conversationFeed instanceof HTMLElement) {
      conversationFeed.scroll({
        behavior: "smooth",
        top: conversationFeed.scrollHeight,
      });
    }
  };

  useEffect(() => {
    scrollDownConversationFeed();
  }, [feedMessages]);

  return (
    <div id={conversationFeedId}>
      {feedMessages.length === 0 && (
        <div className="conversation-welcome-message">
          <Typography variant="h3">
            Welcome, {keycloakService.getUsername()}!
          </Typography>
          <Typography>
            Submit your first prompt to start new conversation
          </Typography>
        </div>
      )}
      {feedMessages.map(({ text, isUserMessage, id }) => (
        <ChatMessage key={id} text={text} isUserMessage={isUserMessage} />
      ))}
    </div>
  );
};

export default ConversationFeed;
