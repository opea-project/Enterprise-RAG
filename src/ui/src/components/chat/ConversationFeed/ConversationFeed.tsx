// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ConversationFeed.scss";

import { useEffect, useRef, useState } from "react";

import BotMessage from "@/components/chat/BotMessage/BotMessage";
import UserMessage from "@/components/chat/UserMessage/UserMessage";
import {
  selectIsStreaming,
  selectMessages,
} from "@/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";

const ConversationFeed = () => {
  const feedMessages = useAppSelector(selectMessages);
  const isStreaming = useAppSelector(selectIsStreaming);
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
    if (isStreaming) {
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
      className="conversation-feed__wrapper"
      onScrollCapture={handleScroll}
    >
      <div className="conversation-feed">
        {feedMessages.map(({ text, isStreaming, isUserMessage, id }) =>
          isUserMessage ? (
            <UserMessage key={id} text={text} />
          ) : (
            <BotMessage key={id} text={text} isStreaming={isStreaming} />
          ),
        )}
      </div>
    </div>
  );
};

export default ConversationFeed;
