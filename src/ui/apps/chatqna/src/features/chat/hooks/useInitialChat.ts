// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEventHandler, useState } from "react";
import { useNavigate } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

import { paths } from "@/config/paths";
import { usePostPromptMutation } from "@/features/chat/api/chatQnA";
import { ABORT_ERROR_MESSAGE } from "@/features/chat/config/api";
import { useChatStreaming } from "@/features/chat/hooks/useChatStreaming";
import { selectIsChatHistorySideMenuOpen } from "@/features/chat/store/chatSideMenus.slice";
import { useAppSelector } from "@/store/hooks";
import { ChatTurn } from "@/types";

let abortController: AbortController | null = null;

const useInitialChat = () => {
  // RTK Query hooks
  const [postPrompt] = usePostPromptMutation();

  // React Router hooks
  const navigate = useNavigate();

  // Redux hooks
  const isChatHistorySideMenuOpen = useAppSelector(
    selectIsChatHistorySideMenuOpen,
  );

  // Streaming utilities
  const {
    resetStreamingRefs,
    createStreamingCallbacks,
    saveChatAndFetch,
    handleStreamingError,
  } = useChatStreaming({
    onNavigateToChat: (id) => navigate(`${paths.chat}/${id}`),
  });

  // Local state for temporary chat
  const [userInput, setUserInput] = useState("");
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);
  const [isChatResponsePending, setIsChatResponsePending] = useState(false);

  const onRequestAbort = () => {
    if (!abortController) {
      return;
    }
    abortController.abort(ABORT_ERROR_MESSAGE);
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

    abortController = new AbortController();
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
      signal: abortController.signal,
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
    isChatHistorySideMenuOpen,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  };
};

export default useInitialChat;
