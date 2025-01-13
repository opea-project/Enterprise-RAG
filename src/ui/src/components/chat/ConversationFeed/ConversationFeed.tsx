// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ConversationFeed.scss";

import { useEffect, useRef, useState } from "react";

import ChatMessage from "@/components/chat/ChatMessage/ChatMessage";
import keycloakService from "@/services/keycloakService";
import {
  selectIsMessageStreamed,
  selectMessages,
} from "@/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";

const ConversationFeed = () => {
  const feedMessages = useAppSelector(selectMessages);
  const isMessageStreamed = useAppSelector(selectIsMessageStreamed);
  const conversationFeedRef = useRef<HTMLDivElement>(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState(true);

  const scrollConversationFeed = (behavior: ScrollBehavior) => {
    if (conversationFeedRef.current) {
      conversationFeedRef.current.scroll({
        behavior,
        top: conversationFeedRef.current.scrollHeight,
      });
    }
  };

  useEffect(() => {
    scrollConversationFeed("instant");
  }, []);

  useEffect(() => {
    if (isAutoScrollEnabled) {
      scrollConversationFeed("smooth");
    }
  }, [feedMessages, isAutoScrollEnabled]);

  useEffect(() => {
    let timeout: string | number | NodeJS.Timeout | undefined;
    if (!isAutoScrollEnabled) {
      timeout = setTimeout(() => {
        setIsAutoScrollEnabled(true);
      }, 5000);
    }
    return () => {
      clearTimeout(timeout);
    };
  }, [isAutoScrollEnabled]);

  const handleScroll = () => {
    if (isMessageStreamed) {
      if (conversationFeedRef.current) {
        const { clientHeight, scrollTop, scrollHeight } =
          conversationFeedRef.current;
        const isScrolledUp = scrollHeight - scrollTop !== clientHeight;
        setIsAutoScrollEnabled(!isScrolledUp);
      }
    } else {
      setIsAutoScrollEnabled(true);
    }
  };

  return (
    <div
      ref={conversationFeedRef}
      className="conversation-feed"
      onScrollCapture={handleScroll}
    >
      {feedMessages.length === 0 && (
        <div className="px-4">
          <h3 className="welcome-message">
            Welcome, {keycloakService.getUsername()}!
          </h3>
          <p>Send your first prompt to start new conversation</p>
        </div>
      )}
      {feedMessages.map(({ text, isUserMessage, id }) => (
        <ChatMessage key={id} text={text} isUserMessage={isUserMessage} />
      ))}
    </div>
  );
};

export default ConversationFeed;
