// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEventHandler, useEffect, useRef } from "react";
import { useSelector } from "react-redux";
import { v4 as uuidv4 } from "uuid";

import {
  UseGetAllChatsQuery,
  UseLazyGetChatByIdQuery,
} from "@/api/chatHistory.api";
import { ABORT_ERROR_MESSAGE } from "@/api/config";
import { UsePostPromptMutation } from "@/api/qna.api";
import {
  useChatStreaming,
  UseChatStreamingConfig,
} from "@/hooks/useChatStreaming";
import {
  addChat,
  addChatTurn,
  ChatHistoryState,
  selectChatById,
  setChatInputValue,
  updateChatTurnAnswer,
  updateChatTurnError,
  updateChatTurnIsPending,
  updateChatTurnSources,
} from "@/store/chatHistory.slice";
import { GetChatByIdResponse } from "@/types/api";
import { createChatTurnsFromHistory } from "@/utils";

export interface UseChatConfig {
  usePostPromptMutation: UsePostPromptMutation;
  useGetAllChatsQuery: UseGetAllChatsQuery;
  useLazyGetChatByIdQuery: UseLazyGetChatByIdQuery;
  streamingConfig: UseChatStreamingConfig;
  useAppSelector: typeof useSelector;
  currentChatId: string | undefined;
  isChatSideMenuOpen: boolean;
  onNavigate?: (path: string) => void;
  onNavigateToChat?: (chatId: string) => void;
  onChatIdChange?: (chatId: string | null) => void;
}

export const useChat = (config: UseChatConfig) => {
  const {
    usePostPromptMutation,
    useGetAllChatsQuery,
    useLazyGetChatByIdQuery,
    streamingConfig,
    useAppSelector,
    currentChatId,
    isChatSideMenuOpen,
    onNavigate,
    onNavigateToChat,
    onChatIdChange,
  } = config;

  const { dispatch } = streamingConfig;

  // RTK Query hooks
  const [postPrompt] = usePostPromptMutation();
  useGetAllChatsQuery();
  const [getChatById] = useLazyGetChatByIdQuery();

  // Streaming utilities
  const {
    resetStreamingRefs,
    createStreamingCallbacks,
    saveChatAndFetch,
    handleStreamingError,
  } = useChatStreaming(streamingConfig);

  // Current chat data derived from Redux store
  const currentChat = useAppSelector((state) =>
    selectChatById(state as { chatHistory: ChatHistoryState }, currentChatId),
  );
  const userInput = currentChat?.inputValue ?? "";
  const currentChatTurns = currentChat?.turns ?? [];
  const lastTurn = currentChatTurns[currentChatTurns.length - 1];
  const isChatResponsePending = lastTurn?.isPending ?? false;

  // Internal AbortController management
  const abortControllerRef = useRef<AbortController | null>(null);

  // Update last selected chat ID when it changes
  useEffect(() => {
    if (currentChatId) {
      onChatIdChange?.(currentChatId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentChatId]);

  // Load chat data when navigating to a specific chat
  useEffect(() => {
    if (currentChatId && !currentChat) {
      getChatById({ id: currentChatId })
        .unwrap()
        .then((getChatHistoryByIdData: GetChatByIdResponse) => {
          if (!getChatHistoryByIdData) {
            onNavigate?.("/chat");
            return;
          }
          const chatTurns = createChatTurnsFromHistory(
            getChatHistoryByIdData.history ?? [],
          );
          // Add the chat to Redux if it doesn't exist
          dispatch(
            addChat({
              id: currentChatId,
              title: getChatHistoryByIdData.historyName ?? "New Chat",
              turns: chatTurns,
              inputValue: "",
            }),
          );
        })
        .catch((error: unknown) => {
          console.error("Failed fetching chat history for ID:", currentChatId);
          console.error("Error:", error);
          onNavigate?.("/chat");
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentChatId, currentChat, getChatById]);

  const onRequestAbort = () => {
    if (!abortControllerRef.current) {
      return;
    }
    abortControllerRef.current.abort(ABORT_ERROR_MESSAGE);
    // isPending will be set to false by the finally block in onPromptSubmit
  };

  const onNewChat = () => {
    if (isChatResponsePending) {
      onRequestAbort();
    }

    onChatIdChange?.(null);
    onNavigate?.("/chat");
  };

  const onPromptChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    if (currentChatId) {
      dispatch(
        setChatInputValue({
          id: currentChatId,
          inputValue: event.target.value,
        }),
      );
    }
  };

  const onPromptSubmit = async () => {
    const sanitizedUserInput = sanitizeString(userInput);

    const conversationTurnId = uuidv4();
    let activeChatId = currentChatId;

    // Defensive check: This should never be null since useChat is only used with /chat/:chatId route,
    // but keeping as safety measure against edge cases (race conditions, future route changes, etc.)
    if (!activeChatId) {
      const newChatId = uuidv4();
      dispatch(
        addChat({
          id: newChatId,
          title: sanitizedUserInput.slice(0, 50),
          turns: [],
          inputValue: "",
        }),
      );
      activeChatId = newChatId;
    } else {
      dispatch(
        setChatInputValue({
          id: activeChatId,
          inputValue: "",
        }),
      );
    }

    dispatch(
      addChatTurn({
        chatId: activeChatId,
        turn: { id: conversationTurnId, question: sanitizedUserInput },
      }),
    );

    abortControllerRef.current = new AbortController();
    resetStreamingRefs();

    const { onAnswerUpdate, onSourcesUpdate } = createStreamingCallbacks(
      // Update local state with answer chunk
      (answer) => {
        dispatch(
          updateChatTurnAnswer({
            chatId: activeChatId,
            turnId: conversationTurnId,
            answerChunk: answer,
          }),
        );
      },
      // Update local state with sources
      (sources) => {
        dispatch(
          updateChatTurnSources({
            chatId: activeChatId,
            turnId: conversationTurnId,
            sources,
          }),
        );
      },
    );

    const { error } = await postPrompt({
      prompt: sanitizedUserInput,
      id: activeChatId,
      signal: abortControllerRef.current.signal,
      onAnswerUpdate,
      onSourcesUpdate,
    }).finally(() => {
      dispatch(
        updateChatTurnIsPending({
          chatId: activeChatId,
          turnId: conversationTurnId,
          isPending: false,
        }),
      );
    });

    const shouldSave = handleStreamingError(
      error,
      // Guardrails error - update Redux
      (errorData) => {
        dispatch(
          updateChatTurnAnswer({
            chatId: activeChatId,
            turnId: conversationTurnId,
            answerChunk: errorData,
          }),
        );
      },
      // Other error - update Redux with error
      (errorData) => {
        dispatch(
          updateChatTurnError({
            chatId: activeChatId,
            turnId: conversationTurnId,
            error: errorData,
          }),
        );
      },
    );

    if (shouldSave) {
      const savedChatId = await saveChatAndFetch(
        sanitizedUserInput,
        activeChatId,
      );

      // Navigate to the chat if it's a new chat
      if (savedChatId && !currentChatId) {
        onNavigateToChat?.(savedChatId);
      }
    }
  };

  return {
    userInput,
    chatTurns: currentChatTurns,
    isChatResponsePending,
    isChatSideMenuOpen,
    onNewChat,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  };
};
