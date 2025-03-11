// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInput.scss";

import {
  ChangeEventHandler,
  FormEventHandler,
  KeyboardEventHandler,
  MouseEventHandler,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import PromptInputButton from "@/features/chat/components/PromptInputButton/PromptInputButton";
import { promptMaxLength } from "@/features/chat/config/promptInput";
import {
  addNewBotMessage,
  addNewUserMessage,
  selectAbortController,
  selectIsStreaming,
  sendPrompt,
} from "@/features/chat/store/conversationFeed.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";

const PromptInput = () => {
  const promptInputRef = useRef<HTMLTextAreaElement | null>(null);
  const [prompt, setPrompt] = useState("");

  const dispatch = useAppDispatch();
  const isStreaming = useAppSelector(selectIsStreaming);
  const abortController = useAppSelector(selectAbortController);

  useEffect(() => {
    focusPromptInput();
  }, []);

  useEffect(() => {
    recalcuatePromptInputHeight();
  }, [prompt]);

  const focusPromptInput = () => {
    promptInputRef.current!.focus();
  };

  const recalcuatePromptInputHeight = () => {
    const promptInput = promptInputRef.current;
    if (promptInput !== null) {
      promptInput.style.height = "auto";
      promptInput.style.height = `${promptInput.scrollHeight}px`;
    }
  };

  const isSubmitDisabled = useCallback(() => {
    const sanitizedPrompt = sanitizeString(prompt).trim();
    const isPromptEmpty = sanitizedPrompt.length === 0;
    const isPromptMaxLengthExceeded = sanitizedPrompt.length > promptMaxLength;

    return isPromptEmpty || isPromptMaxLengthExceeded;
  }, [prompt]);

  const submitPrompt = async () => {
    const sanitizedPrompt = sanitizeString(prompt);
    dispatch(addNewUserMessage(sanitizedPrompt));
    dispatch(addNewBotMessage());
    dispatch(sendPrompt(sanitizedPrompt));

    setPrompt("");
    focusPromptInput();
  };

  const handleSubmit: FormEventHandler<HTMLFormElement> = async (event) => {
    event.preventDefault();
    submitPrompt();
  };

  const handleChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    setPrompt(event.target.value);
  };

  const handleKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isSubmitDisabled() && !isStreaming) {
        submitPrompt();
      }
    }
  };

  const stopStreaming = () => {
    abortController?.abort(""); // empty string set for further error handling
  };

  const handleStopBtnClick: MouseEventHandler = (event) => {
    event.preventDefault();
    stopStreaming();
    focusPromptInput();
  };

  const handleStopBtnKeyDown: KeyboardEventHandler = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      stopStreaming();
      focusPromptInput();
    }
  };

  const promptInputButton = isStreaming ? (
    <PromptInputButton
      icon="prompt-stop"
      type="button"
      onClick={handleStopBtnClick}
      onKeyDown={handleStopBtnKeyDown}
    />
  ) : (
    <PromptInputButton
      icon="prompt-send"
      type="submit"
      disabled={isSubmitDisabled()}
    />
  );

  return (
    <form className="prompt-input__form" onSubmit={handleSubmit}>
      <textarea
        ref={promptInputRef}
        value={prompt}
        name="prompt-input"
        placeholder="Enter your prompt..."
        className="prompt-input"
        rows={1}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
      />
      {promptInputButton}
    </form>
  );
};

export default PromptInput;
