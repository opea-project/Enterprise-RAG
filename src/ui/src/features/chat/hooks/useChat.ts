// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEventHandler } from "react";
import { v4 as uuidv4 } from "uuid";

import { usePostPromptMutation } from "@/features/chat/api";
import { ABORT_ERROR_MESSAGE, HTTP_ERRORS } from "@/features/chat/config/api";
import {
  addNewConversationTurn,
  resetConversationFeedSlice,
  selectConversationTurns,
  selectIsChatResponsePending,
  selectUserInput,
  setIsChatResponsePending,
  setUserInput,
  updateAnswer,
  updateError,
  updateIsPending,
} from "@/features/chat/store/conversationFeed.slice";
import {
  getValidConversationHistory,
  isChatErrorResponse,
  isChatErrorResponseDataString,
} from "@/features/chat/utils/api";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { ConversationTurn } from "@/types";
import { sanitizeString } from "@/utils";

let abortController: AbortController | null = null;

const useChat = () => {
  const [postPrompt] = usePostPromptMutation();
  const dispatch = useAppDispatch();

  const userInput = useAppSelector(selectUserInput);
  const conversationTurns = useAppSelector(selectConversationTurns);
  const isChatResponsePending = useAppSelector(selectIsChatResponsePending);

  const onPromptChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    dispatch(setUserInput(event.target.value));
  };

  const onPromptSubmit = async () => {
    const sanitizedUserInput = sanitizeString(userInput);
    dispatch(setUserInput(""));

    const conversationTurnId = uuidv4();
    dispatch(
      addNewConversationTurn({
        id: conversationTurnId,
        question: sanitizedUserInput,
      }),
    );

    dispatch(setIsChatResponsePending(true));

    abortController = new AbortController();
    const conversationHistory = getValidConversationHistory(conversationTurns);

    const { error } = await postPrompt({
      prompt: sanitizedUserInput,
      conversationHistory,
      signal: abortController.signal,
      onAnswerUpdate: (answer: ConversationTurn["answer"]) => {
        dispatch(updateAnswer(answer));
      },
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

    dispatch(resetConversationFeedSlice());
  };

  return {
    userInput,
    conversationTurns,
    isChatResponsePending,
    onNewChat,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  };
};

export default useChat;
