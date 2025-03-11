// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ConversationFeed.scss";

import debounce from "lodash.debounce";
import { useCallback, useEffect, useRef, useState } from "react";

import BotMessage from "@/features/chat/components/BotMessage/BotMessage";
import ScrollToBottomButton from "@/features/chat/components/ScrollToBottomButton/ScrollToBottomButton";
import UserMessage from "@/features/chat/components/UserMessage/UserMessage";
import { bottomMargin } from "@/features/chat/config/conversationFeed";
import { selectMessages } from "@/features/chat/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";

const ConversationFeed = () => {
  const messages = useAppSelector(selectMessages);
  const conversationFeedRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [showScrollToBottomBtn, setShowScrollToBottomBtn] = useState(false);

  const debouncedScrollToBottom = useCallback(
    debounce((behavior: ScrollBehavior) => {
      if (conversationFeedRef.current) {
        conversationFeedRef.current.scroll({
          behavior,
          top: conversationFeedRef.current.scrollHeight,
        });
      }
    }, 50),
    [conversationFeedRef.current?.scrollHeight],
  );

  const isAtBottom = useCallback(() => {
    if (conversationFeedRef.current) {
      const { scrollTop, scrollHeight, clientHeight } =
        conversationFeedRef.current;
      return scrollHeight - scrollTop <= clientHeight + bottomMargin;
    }
    return false;
  }, [
    conversationFeedRef.current?.scrollHeight,
    conversationFeedRef.current?.scrollTop,
    conversationFeedRef.current?.clientHeight,
  ]);

  const debouncedScrollToBottomButtonUpdate = useCallback(
    debounce(() => {
      setShowScrollToBottomBtn(!isAtBottom());
    }, 100),
    [isAtBottom],
  );

  useEffect(() => {
    debouncedScrollToBottom("instant");
  }, []);

  useEffect(() => {
    debouncedScrollToBottom("instant");
  }, [messages.length]);

  useEffect(() => {
    if (isAtBottom() && !isUserScrolling) {
      debouncedScrollToBottom("smooth");
    }
  }, [messages, isUserScrolling]);

  const handleWheel = useCallback(
    (event: WheelEvent) => {
      if (event.deltaY < 0) {
        setIsUserScrolling(true);
      } else if (event.deltaY > 0 && isAtBottom()) {
        setIsUserScrolling(false);
      }
    },
    [isAtBottom],
  );

  useEffect(() => {
    const conversationFeedElement = conversationFeedRef.current;
    if (conversationFeedElement) {
      conversationFeedElement.addEventListener("wheel", handleWheel, {
        passive: true,
      });
    }

    return () => {
      if (conversationFeedElement) {
        conversationFeedElement.removeEventListener("wheel", handleWheel);
      }
    };
  }, [handleWheel]);

  useEffect(() => {
    if (conversationFeedRef.current) {
      debouncedScrollToBottomButtonUpdate();
    }
  }, [
    conversationFeedRef.current?.scrollHeight,
    conversationFeedRef.current?.scrollTop,
    conversationFeedRef.current?.clientHeight,
  ]);

  useEffect(() => {
    return () => {
      debouncedScrollToBottom.cancel();
      debouncedScrollToBottomButtonUpdate.cancel();
    };
  }, [debouncedScrollToBottom, debouncedScrollToBottomButtonUpdate]);

  const handleScroll = useCallback(() => {
    debouncedScrollToBottomButtonUpdate();
  }, [debouncedScrollToBottomButtonUpdate]);

  return (
    <div className="conversation-feed__wrapper">
      <div
        ref={conversationFeedRef}
        onScroll={handleScroll}
        className="conversation-feed__scroll"
      >
        <div className="conversation-feed">
          {messages.map(({ text, isStreaming, isUserMessage, id, isError }) =>
            isUserMessage ? (
              <UserMessage key={id} text={text} />
            ) : (
              <BotMessage
                key={id}
                text={text}
                isStreaming={isStreaming}
                isError={isError}
              />
            ),
          )}
        </div>
      </div>
      <ScrollToBottomButton
        show={showScrollToBottomBtn}
        onClick={() => debouncedScrollToBottom("smooth")}
      />
    </div>
  );
};

export default ConversationFeed;
