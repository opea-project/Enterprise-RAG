// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEventHandler, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

import { paths } from "@/config/paths";
import {
  useGetAllChatsQuery,
  useLazyGetChatByIdQuery,
} from "@/features/chat/api/chatHistory";
import { usePostPromptMutation } from "@/features/chat/api/chatQnA";
import { ABORT_ERROR_MESSAGE } from "@/features/chat/config/api";
import { useChatStreaming } from "@/features/chat/hooks/useChatStreaming";
import {
  addChat,
  addChatTurn,
  setChatInputValue,
  updateChatTurnAnswer,
  updateChatTurnError,
  updateChatTurnIsPending,
  updateChatTurnSources,
} from "@/features/chat/store/chatHistory.slice";
import { selectIsChatHistorySideMenuOpen } from "@/features/chat/store/chatSideMenus.slice";
import { createChatTurnsFromHistory } from "@/features/chat/utils";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setLastSelectedChatId } from "@/store/viewNavigation.slice";

let abortController: AbortController | null = null;

const useChat = () => {
  // RTK Query hooks
  // Chat QnA API hooks
  const [postPrompt] = usePostPromptMutation();

  // Chat History API hooks
  useGetAllChatsQuery();
  const [getChatById] = useLazyGetChatByIdQuery();

  // React Router hooks
  const navigate = useNavigate();
  const { chatId: chatIdFromParams } = useParams<{ chatId?: string }>();

  // Redux hooks
  const dispatch = useAppDispatch();
  const isChatHistorySideMenuOpen = useAppSelector(
    selectIsChatHistorySideMenuOpen,
  );

  // Streaming utilities
  const {
    resetStreamingRefs,
    createStreamingCallbacks,
    saveChatAndFetch,
    handleStreamingError,
  } = useChatStreaming();

  // Current chat data derived from Redux store and URL params
  const currentChatId = chatIdFromParams ?? null;
  const currentChat = useAppSelector((state) =>
    state.chatHistory.chats.find((chat) => chat.id === currentChatId),
  );
  const userInput = currentChat?.inputValue ?? "";
  const currentChatTurns = currentChat?.turns ?? [];
  const lastTurn = currentChatTurns[currentChatTurns.length - 1];
  const isChatResponsePending = lastTurn?.isPending ?? false;

  // Update last selected chat ID when it changes
  useEffect(() => {
    if (currentChatId) {
      dispatch(setLastSelectedChatId(currentChatId));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentChatId]);

  // Load chat data when navigating to a specific chat
  useEffect(() => {
    if (currentChatId && !currentChat) {
      getChatById({ id: currentChatId })
        .unwrap()
        .then((getChatHistoryByIdData) => {
          if (!getChatHistoryByIdData) {
            navigate(paths.chat);
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
        .catch((error) => {
          console.error("Failed fetching chat history for ID:", currentChatId);
          console.error("Error:", error);
          navigate(paths.chat);
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentChatId, currentChat, getChatById, navigate]);

  const onRequestAbort = () => {
    if (!abortController) {
      return;
    }
    abortController.abort(ABORT_ERROR_MESSAGE);
    // isPending will be set to false by the finally block in onPromptSubmit
  };

  const onNewChat = () => {
    if (isChatResponsePending) {
      onRequestAbort();
    }

    dispatch(setLastSelectedChatId(null));
    navigate(paths.chat);
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

    abortController = new AbortController();
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
      signal: abortController.signal,
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
      if (savedChatId && currentChatId === null) {
        navigate(`${paths.chat}/${savedChatId}`);
      }
    }
  };

  return {
    userInput,
    chatTurns: currentChatTurns,
    isChatResponsePending,
    isChatHistorySideMenuOpen,
    onNewChat,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  };
};

export default useChat;
