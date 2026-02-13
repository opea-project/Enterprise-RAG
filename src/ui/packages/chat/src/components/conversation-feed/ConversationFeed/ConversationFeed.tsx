// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ConversationFeed.scss";

import classNames from "classnames";
import debounce from "lodash.debounce";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";

import { MemoizedBotMessage as BotMessage } from "@/components/conversation-feed/BotMessage/BotMessage";
import { PlaySpeechButtonState } from "@/components/conversation-feed/PlaySpeechButton/PlaySpeechButton";
import { ScrollToBottomButton } from "@/components/conversation-feed/ScrollToBottomButton/ScrollToBottomButton";
import { MemoizedUserMessage as UserMessage } from "@/components/conversation-feed/UserMessage/UserMessage";
import { ChatTurn } from "@/types";

const bottomMargin = 80; // margin to handle bottom scroll detection

interface ConversationFeedProps {
  conversationTurns: ChatTurn[];
  playingTurnId?: string | null;
  playingState?: PlaySpeechButtonState;
  onFileDownload: (fileName: string, bucketName: string) => void;
  onPlayMessage?: (turnId: string) => Promise<void>;
}

export const ConversationFeed = ({
  conversationTurns,
  playingTurnId,
  playingState,
  onFileDownload,
  onPlayMessage,
}: ConversationFeedProps) => {
  const conversationFeedRef = useRef<HTMLDivElement>(null);
  const [showScrollToBottomBtn, setShowScrollToBottomBtn] = useState(false);
  const prevConversationLengthRef = useRef<number>(0);
  const pendingTurnRef = useRef<HTMLDivElement>(null);

  const debouncedScrollToBottom = useRef(
    debounce((behavior: ScrollBehavior) => {
      if (conversationFeedRef.current) {
        conversationFeedRef.current.scroll({
          behavior,
          top: conversationFeedRef.current.scrollHeight,
        });
      }
    }, 50),
  ).current;

  const debouncedScrollToBottomButtonUpdate = useRef(
    debounce(() => {
      if (conversationFeedRef.current) {
        const { scrollTop, scrollHeight, clientHeight } =
          conversationFeedRef.current;
        const atBottom =
          scrollHeight - scrollTop <= clientHeight + bottomMargin;
        setShowScrollToBottomBtn(!atBottom);
      }
    }, 100),
  ).current;

  // Only scroll when a new turn is added (conversation length increases)
  useEffect(() => {
    const currentLength = conversationTurns.length;
    const prevLength = prevConversationLengthRef.current;

    // Scroll only when a new turn is added, not on initial render or streaming updates
    if (prevLength > 0 && currentLength > prevLength) {
      debouncedScrollToBottom("instant");
    }

    prevConversationLengthRef.current = currentLength;
  }, [conversationTurns.length, debouncedScrollToBottom]);

  useEffect(() => {
    if (conversationFeedRef.current) {
      debouncedScrollToBottomButtonUpdate();
    }
  }, [
    conversationFeedRef.current?.scrollHeight,
    conversationFeedRef.current?.scrollTop,
    conversationFeedRef.current?.clientHeight,
    debouncedScrollToBottomButtonUpdate,
  ]);

  // Set margin-bottom on pending turn programmatically to push user message to top
  useLayoutEffect(() => {
    const pendingTurn = conversationTurns.find((turn) => turn.isPending);
    // Apply margin while turn is pending (includes waiting and streaming phases)
    const shouldApplyMargin = !!pendingTurn;

    const updatePendingTurnSpacing = () => {
      if (
        pendingTurnRef.current &&
        conversationFeedRef.current &&
        shouldApplyMargin
      ) {
        const feedClientHeight = conversationFeedRef.current.clientHeight;
        const pendingTurnHeight =
          pendingTurnRef.current.getBoundingClientRect().height;

        // Calculate margin needed: visible height - actual content height
        const BOT_MESSAGE_MARGIN_BOTTOM = 32;
        const marginBottom = Math.max(
          0,
          feedClientHeight - pendingTurnHeight - BOT_MESSAGE_MARGIN_BOTTOM,
        );
        pendingTurnRef.current.style.marginBottom = `${marginBottom}px`;
      }
    };

    // Update immediately
    updatePendingTurnSpacing();

    // If no pending turn, find and remove margin from all turns
    if (!shouldApplyMargin && conversationFeedRef.current) {
      const allTurns =
        conversationFeedRef.current.querySelectorAll(".conversation-turn");
      allTurns.forEach((turn) => {
        (turn as HTMLElement).style.marginBottom = "";
      });
    }

    // Only observe if we should apply margin
    if (!shouldApplyMargin) {
      return;
    }

    // Also update on resize
    const resizeObserver = new ResizeObserver(updatePendingTurnSpacing);
    if (conversationFeedRef.current) {
      resizeObserver.observe(conversationFeedRef.current);
    }

    // Observe pending turn for content changes
    if (pendingTurnRef.current) {
      resizeObserver.observe(pendingTurnRef.current);
    }

    return () => {
      resizeObserver.disconnect();
      // Don't reset margin in cleanup - let the next effect handle it
      // This prevents margin flicker during streaming updates
    };
  }, [conversationTurns]);

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
            ({ id, question, answer, error, isPending, sources }) => {
              // Only pass active state if this turn matches the current playing turn
              const messagePlayingState: PlaySpeechButtonState =
                playingTurnId === id ? (playingState ?? "idle") : "idle";

              return (
                <div
                  key={id}
                  ref={isPending ? pendingTurnRef : null}
                  className={classNames("conversation-turn", {
                    "conversation-turn--pending": isPending,
                  })}
                >
                  <UserMessage question={question} />
                  <BotMessage
                    id={id}
                    answer={answer}
                    isPending={isPending}
                    error={error}
                    sources={sources}
                    onFileDownload={onFileDownload}
                    onPlayMessage={onPlayMessage}
                    playingState={messagePlayingState}
                  />
                </div>
              );
            },
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
