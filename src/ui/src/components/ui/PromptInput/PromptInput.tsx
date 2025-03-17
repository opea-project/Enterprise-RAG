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
} from "react";

import PromptInputButton from "@/components/ui/PromptInputButton/PromptInputButton";
import { promptMaxLength } from "@/config/promptInput";
import {
  selectAbortController,
  selectIsStreaming,
} from "@/features/chat/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";

interface PromptInputProps {
  prompt: string;
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  onSubmit: (prompt: string) => void;
}

const PromptInput = ({ prompt, onChange, onSubmit }: PromptInputProps) => {
  const promptInputRef = useRef<HTMLTextAreaElement | null>(null);

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

  const submitPrompt = () => {
    const sanitizedPrompt = sanitizeString(prompt).trim();
    onSubmit(sanitizedPrompt);

    focusPromptInput();
  };

  const handleSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    submitPrompt();
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
        onChange={onChange}
        onKeyDown={handleKeyDown}
      />
      {promptInputButton}
    </form>
  );
};

export default PromptInput;
