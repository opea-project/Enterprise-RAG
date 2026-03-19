// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEventHandler, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import { ABORT_ERROR_MESSAGE } from "@/api/config";
import { UsePostPromptMutation } from "@/api/qna.api";
import {
  useChatStreaming,
  UseChatStreamingConfig,
} from "@/hooks/useChatStreaming";
import { ChatTurn } from "@/types";

export interface UseInitialChatConfig {
  usePostPromptMutation: UsePostPromptMutation;
  streamingConfig: UseChatStreamingConfig;
  isChatSideMenuOpen: boolean;
  onNavigateToChat?: (chatId: string) => void;
}

export const useInitialChat = (config: UseInitialChatConfig) => {
  const {
    usePostPromptMutation,
    streamingConfig,
    isChatSideMenuOpen,
    onNavigateToChat,
  } = config;

  // RTK Query hooks
  const [postPrompt] = usePostPromptMutation();

  // Streaming utilities
  const {
    resetStreamingRefs,
    createStreamingCallbacks,
    saveChatAndFetch,
    handleStreamingError,
  } = useChatStreaming({
    ...streamingConfig,
    onNavigateToChat,
  });

  // Local state for temporary chat
  const [userInput, setUserInput] = useState("");
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);
  const [isChatResponsePending, setIsChatResponsePending] = useState(false);

  // Internal AbortController management
  const abortControllerRef = useRef<AbortController | null>(null);

  const onRequestAbort = () => {
    if (!abortControllerRef.current) {
      return;
    }
    abortControllerRef.current.abort(ABORT_ERROR_MESSAGE);
    setIsChatResponsePending(false);
  };

  const onPromptChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    setUserInput(event.target.value);
  };

  const onPromptSubmit = async () => {
    const sanitizedUserInput = sanitizeString(userInput);
    setUserInput("");

    const conversationTurnId = uuidv4();

    const newTurn: ChatTurn = {
      id: conversationTurnId,
      question: sanitizedUserInput,
      answer: "",
      error: null,
      isPending: true,
      sources: [],
    };

    setChatTurns([newTurn]);
    setIsChatResponsePending(true);

    abortControllerRef.current = new AbortController();
    resetStreamingRefs();

    const { onAnswerUpdate, onSourcesUpdate } = createStreamingCallbacks(
      // Update local state with answer chunk
      (answer) => {
        setChatTurns((prevTurns) =>
          prevTurns.map((turn) =>
            turn.id === conversationTurnId
              ? { ...turn, answer: turn.answer + answer }
              : turn,
          ),
        );
      },
      // Update local state with sources
      (sources) => {
        setChatTurns((prevTurns) =>
          prevTurns.map((turn) =>
            turn.id === conversationTurnId ? { ...turn, sources } : turn,
          ),
        );
      },
    );

    const { error } = await postPrompt({
      prompt: sanitizedUserInput,
      signal: abortControllerRef.current.signal,
      onAnswerUpdate,
      onSourcesUpdate,
    }).finally(() => {
      // Mark turn as not pending
      setChatTurns((prevTurns) =>
        prevTurns.map((turn) =>
          turn.id === conversationTurnId ? { ...turn, isPending: false } : turn,
        ),
      );
      setIsChatResponsePending(false);
    });

    // Handle errors using the utility
    const shouldSave = handleStreamingError(
      error,
      (errorData) => {
        // Guardrails error - update local state
        setChatTurns((prevTurns) =>
          prevTurns.map((turn) =>
            turn.id === conversationTurnId
              ? {
                  ...turn,
                  answer: (turn.answer || "") + errorData,
                }
              : turn,
          ),
        );
      },
      (errorData) => {
        // Other error - update local state with error
        setChatTurns((prevTurns) =>
          prevTurns.map((turn) =>
            turn.id === conversationTurnId
              ? { ...turn, error: errorData, isPending: false }
              : turn,
          ),
        );
      },
    );

    // Save chat if appropriate
    if (shouldSave) {
      await saveChatAndFetch(sanitizedUserInput);
    }
  };

  return {
    userInput,
    chatTurns,
    isChatResponsePending,
    isChatSideMenuOpen,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  };
};
