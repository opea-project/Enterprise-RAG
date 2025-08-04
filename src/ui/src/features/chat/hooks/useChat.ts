// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEventHandler, useEffect, useMemo, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

import { paths } from "@/config/paths";
import {
  useGetAllChatsQuery,
  useLazyGetChatByIdQuery,
  useSaveChatMutation,
} from "@/features/chat/api/chatHistory";
import { usePostPromptMutation } from "@/features/chat/api/chatQnA";
import { ABORT_ERROR_MESSAGE, HTTP_ERRORS } from "@/features/chat/config/api";
import { selectIsChatHistorySideMenuOpen } from "@/features/chat/store/chatSideMenus.slice";
import {
  addNewChatTurn,
  resetCurrentChatSlice,
  selectCurrentChatId,
  selectCurrentChatSources,
  selectCurrentChatTurns,
  selectIsChatResponsePending,
  selectUserInput,
  setCurrentChatId,
  setCurrentChatSources,
  setCurrentChatTurns,
  setIsChatResponsePending,
  setUserInput,
  updateAnswer,
  updateError,
  updateIsPending,
  updateSources,
} from "@/features/chat/store/currentChat.slice";
import {
  AnswerUpdateHandler,
  SourcesUpdateHandler,
} from "@/features/chat/types/api";
import { createChatTurnsFromHistory } from "@/features/chat/utils";
import {
  isChatErrorResponse,
  isChatErrorResponseDataString,
} from "@/features/chat/utils/api";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";

let abortController: AbortController | null = null;

const useChat = () => {
  // RTK Query hooks
  // Chat QnA API hooks
  const [postPrompt] = usePostPromptMutation();

  // Chat History API hooks
  useGetAllChatsQuery();
  const [getChatById] = useLazyGetChatByIdQuery();
  const [saveChat] = useSaveChatMutation();

  // React Router hooks
  const location = useLocation();
  const navigate = useNavigate();

  // Redux hooks
  const dispatch = useAppDispatch();
  const userInput = useAppSelector(selectUserInput);
  const currentChatTurns = useAppSelector(selectCurrentChatTurns);
  const currentChatSources = useAppSelector(selectCurrentChatSources);
  const currentChatId = useAppSelector(selectCurrentChatId);
  const isChatResponsePending = useAppSelector(selectIsChatResponsePending);
  const isChatHistorySideMenuOpen = useAppSelector(
    selectIsChatHistorySideMenuOpen,
  );

  const currentAnswerRef = useRef("");

  useEffect(() => {
    if (location.pathname !== paths.chat) {
      const chatIdFromPath = location.pathname.split("/")[2];
      if (chatIdFromPath) {
        getChatById({ id: chatIdFromPath })
          .unwrap()
          .then((getChatHistoryByIdData) => {
            if (!getChatHistoryByIdData) {
              dispatch(resetCurrentChatSlice());
              navigate(paths.chat);
              return;
            }
            dispatch(setCurrentChatId(chatIdFromPath));
            const chatTurns = createChatTurnsFromHistory(
              getChatHistoryByIdData.history || [],
            );
            dispatch(setCurrentChatTurns(chatTurns));

            if (currentChatSources.length === 0) {
              dispatch(setCurrentChatSources(Array(chatTurns.length).fill([])));
            } else if (currentChatSources.length < chatTurns.length) {
              // If sources are not initialized or are less than turns, fill with empty arrays
              dispatch(
                setCurrentChatSources([
                  ...currentChatSources,
                  ...Array(chatTurns.length - currentChatSources.length).fill(
                    [],
                  ),
                ]),
              );
            }
          })
          .catch((error) => {
            console.error(
              "Failed fetching chat history for ID:",
              chatIdFromPath,
            );
            console.error("Error:", error);
            dispatch(resetCurrentChatSlice());
            navigate(paths.chat);
          });
      }
    }
  }, [currentChatSources, dispatch, getChatById, location, navigate]);

  const onPromptChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    dispatch(setUserInput(event.target.value));
  };

  const onSourcesUpdate: SourcesUpdateHandler = (sources) => {
    dispatch(updateSources(sources));
  };

  const afterResponse = () => {
    saveChat({
      id: currentChatId,
      history: [
        {
          question: sanitizeString(userInput),
          answer: currentAnswerRef.current,
        },
      ],
    }).then((response) => {
      if (response.data) {
        const { id } = response.data;
        if (currentChatId === null && currentChatId !== id) {
          dispatch(setCurrentChatId(id));
        } else {
          navigate(`${paths.chat}/${id}`);
        }
      }
    });
  };

  const onAnswerUpdate: AnswerUpdateHandler = (answer) => {
    dispatch(updateAnswer(answer));
    currentAnswerRef.current += answer;
  };

  const onPromptSubmit = async () => {
    const sanitizedUserInput = sanitizeString(userInput);
    dispatch(setUserInput(""));

    const conversationTurnId = uuidv4();
    dispatch(
      addNewChatTurn({
        id: conversationTurnId,
        question: sanitizedUserInput,
      }),
    );

    dispatch(setIsChatResponsePending(true));

    abortController = new AbortController();
    currentAnswerRef.current = "";

    const { error } = await postPrompt({
      prompt: sanitizedUserInput,
      id: currentChatId,
      signal: abortController.signal,
      onAnswerUpdate,
      onSourcesUpdate,
    }).finally(() => {
      dispatch(updateIsPending(false));
      dispatch(setIsChatResponsePending(false));
    });

    if (
      isChatErrorResponse(error) &&
      isChatErrorResponseDataString(error.data)
    ) {
      if (error.status === HTTP_ERRORS.GUARDRAILS_ERROR.statusCode) {
        dispatch(updateAnswer(error.data));
      } else if (
        error.status === HTTP_ERRORS.CLIENT_CLOSED_REQUEST.statusCode
      ) {
        dispatch(updateAnswer(""));
      } else {
        dispatch(updateError(error.data));
      }
    }

    afterResponse();
  };

  const onRequestAbort = () => {
    if (!abortController) {
      return;
    }
    abortController.abort(ABORT_ERROR_MESSAGE);
    dispatch(setIsChatResponsePending(false));
  };

  const onNewChat = () => {
    if (isChatResponsePending) {
      onRequestAbort();
    }

    navigate(paths.chat);
    dispatch(resetCurrentChatSlice());
  };

  const chatTurns = useMemo(
    () =>
      currentChatTurns.map((turn, index) => ({
        ...turn,
        sources: currentChatSources[index] ?? [],
      })),
    [currentChatTurns, currentChatSources],
  );

  return {
    userInput,
    chatTurns,
    isChatResponsePending,
    isChatHistorySideMenuOpen,
    onNewChat,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  };
};

export default useChat;
