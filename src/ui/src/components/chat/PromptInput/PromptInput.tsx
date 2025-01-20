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
import { MdStop } from "react-icons/md";
import { TbArrowUp } from "react-icons/tb";

import PromptInputButton from "@/components/chat/PromptInputButton/PromptInputButton";
import {
  addNewBotMessage,
  addNewUserMessage,
  postPrompt,
  selectAbortController,
  selectIsStreaming,
} from "@/store/conversationFeed.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";

const MAX_REQUEST_BODY_SIZE = 1 * 1024 * 1024; // 1MB in bytes - from default.conf
const REQUEST_BODY_FORMAT_OVERHEAD = '{ "text": "" }'.length;
const PROMPT_MAX_LENGTH = MAX_REQUEST_BODY_SIZE - REQUEST_BODY_FORMAT_OVERHEAD;

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
    const isPromptMaxLengthExceeded =
      sanitizedPrompt.length > PROMPT_MAX_LENGTH;

    return isPromptEmpty || isPromptMaxLengthExceeded;
  }, [prompt]);

  const submitPrompt = async () => {
    const sanitizedPrompt = sanitizeString(prompt);
    dispatch(addNewUserMessage(sanitizedPrompt));
    dispatch(addNewBotMessage());
    dispatch(postPrompt(sanitizedPrompt));

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
      icon={<MdStop />}
      type="button"
      onClick={handleStopBtnClick}
      onKeyDown={handleStopBtnKeyDown}
    />
  ) : (
    <PromptInputButton
      icon={<TbArrowUp />}
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
