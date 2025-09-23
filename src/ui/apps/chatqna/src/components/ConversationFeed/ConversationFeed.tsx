// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ConversationFeed.scss";

import debounce from "lodash.debounce";
import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";

import BotMessage from "@/components/BotMessage/BotMessage";
import ScrollToBottomButton from "@/components/ScrollToBottomButton/ScrollToBottomButton";
import UserMessage from "@/components/UserMessage/UserMessage";
import { paths } from "@/config/paths";
import { ChatTurn } from "@/types";

const bottomMargin = 80; // margin to handle bottom scroll detection

interface ConversationFeedProps {
  conversationTurns: ChatTurn[];
}

const ConversationFeed = ({ conversationTurns }: ConversationFeedProps) => {
  const conversationFeedRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [showScrollToBottomBtn, setShowScrollToBottomBtn] = useState(false);

  const location = useLocation();

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
    if (location.pathname.startsWith(`${paths.chat}/`)) {
      debouncedScrollToBottom("instant");
    }
  }, [location.pathname, debouncedScrollToBottom]);

  useEffect(() => {
    debouncedScrollToBottom("instant");
  }, [conversationTurns.length]);

  useEffect(() => {
    if (isAtBottom() && !isUserScrolling) {
      debouncedScrollToBottom("smooth");
    }
  }, [conversationTurns, isUserScrolling]);

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
        className="conversation-feed__scroll"
        onScroll={handleScroll}
      >
        <div className="conversation-feed">
          {conversationTurns.map(
            ({ id, question, answer, error, isPending, sources }) => (
              <Fragment key={id}>
                <UserMessage question={question} />
                <BotMessage
                  answer={answer}
                  isPending={isPending}
                  error={error}
                  sources={sources}
                />
              </Fragment>
            ),
          )}
        </div>
      </div>
      <ScrollToBottomButton
        show={showScrollToBottomBtn}
        onPress={() => debouncedScrollToBottom("smooth")}
      />
    </div>
  );
};

export default ConversationFeed;
