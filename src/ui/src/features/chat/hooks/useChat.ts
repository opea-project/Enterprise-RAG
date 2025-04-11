// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEventHandler, useRef } from "react";

import { usePostPromptMutation } from "@/features/chat/api";
import {
  selectIsStreaming,
  selectMessages,
  selectPrompt,
  setPrompt,
  updateBotMessageText,
} from "@/features/chat/store/conversationFeed.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";

export const abortErrorMessage = "User interrupted chatbot response.";

const useChat = () => {
  const [postPrompt] = usePostPromptMutation();
  const prompt = useAppSelector(selectPrompt);
  const dispatch = useAppDispatch();
  const messages = useAppSelector(selectMessages);
  const isStreaming = useAppSelector(selectIsStreaming);
  const abortController = useRef(new AbortController());

  const onPromptSubmit = () => {
    const sanitizedPrompt = sanitizeString(prompt);
    const newAbortController = new AbortController();
    abortController.current = newAbortController;

    postPrompt({
      prompt: sanitizedPrompt,
      signal: abortController.current.signal,
      onMessageTextUpdate: (chunk) => {
        dispatch(updateBotMessageText(chunk));
      },
    });
  };

  const onPromptChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    dispatch(setPrompt(event.target.value));
  };

  const abortRequest = () => {
    abortController.current.abort(abortErrorMessage);
  };

  return {
    messages,
    prompt,
    isStreaming,
    abortRequest,
    onPromptSubmit,
    onPromptChange,
  };
};

export default useChat;
