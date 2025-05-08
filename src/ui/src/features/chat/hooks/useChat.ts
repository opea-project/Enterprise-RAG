// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEventHandler, useRef } from "react";
import { v4 as uuidv4 } from "uuid";

import { usePostPromptMutation } from "@/features/chat/api";
import { ABORT_ERROR_MESSAGE, HTTP_ERRORS } from "@/features/chat/config/api";
import {
  addNewConversationTurn,
  selectConversationTurns,
  selectUserInput,
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

const useChat = () => {
  const [postPrompt, { isLoading: isChatResponsePending }] =
    usePostPromptMutation();
  const dispatch = useAppDispatch();
  const abortController = useRef(new AbortController());

  const userInput = useAppSelector(selectUserInput);
  const conversationTurns = useAppSelector(selectConversationTurns);

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

    const conversationHistory = getValidConversationHistory(conversationTurns);

    const newAbortController = new AbortController();
    abortController.current = newAbortController;

    const { error } = await postPrompt({
      prompt: sanitizedUserInput,
      conversationHistory,
      signal: abortController.current.signal,
      onAnswerUpdate: (answer: ConversationTurn["answer"]) => {
        dispatch(updateAnswer(answer));
      },
    });

    if (
      isChatErrorResponse(error) &&
      isChatErrorResponseDataString(error.data)
    ) {
      if (error.status === HTTP_ERRORS.GUARDRAILS_ERROR.statusCode) {
        dispatch(updateAnswer(error.data));
        dispatch(updateIsPending(false));
      } else if (
        error.status === HTTP_ERRORS.CLIENT_CLOSED_REQUEST.statusCode
      ) {
        dispatch(updateAnswer(""));
        dispatch(updateIsPending(false));
      } else {
        dispatch(updateError(error.data));
      }
    }
  };

  const onRequestAbort = () => {
    abortController.current.abort(ABORT_ERROR_MESSAGE);
  };

  return {
    userInput,
    conversationTurns,
    isChatResponsePending,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  };
};

export default useChat;
