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
import { promptMaxHeight, promptMaxLength } from "@/config/promptInput";
import { sanitizeString } from "@/utils";

interface PromptInputProps {
  prompt: string;
  isStreaming?: boolean;
  abortRequest?: () => void;
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  onSubmit: (prompt: string) => void;
}

const PromptInput = ({
  prompt,
  isStreaming = false,
  abortRequest,
  onChange,
  onSubmit,
}: PromptInputProps) => {
  const promptInputRef = useRef<HTMLTextAreaElement | null>(null);

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
      const currentHeight = promptInput.style.height;
      promptInput.style.height = "auto";
      const targetHeight = `${promptInput.scrollHeight}px`;
      promptInput.style.height = currentHeight;

      const maxHeight = promptMaxHeight;
      const targetHeightNumber = parseInt(targetHeight, 10);
      promptInput.style.overflowY =
        targetHeightNumber > maxHeight ? "scroll" : "hidden";

      requestAnimationFrame(() => {
        promptInput.style.height = targetHeight;
      });
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

  const handleStopBtnClick: MouseEventHandler = (event) => {
    event.preventDefault();
    abortRequest?.();
    focusPromptInput();
  };

  const handleStopBtnKeyDown: KeyboardEventHandler = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      abortRequest?.();
      focusPromptInput();
    }
  };

  const getPromptInputButton = () => {
    if (abortRequest) {
      return isStreaming ? (
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
    } else {
      return (
        <PromptInputButton
          icon="prompt-send"
          type="submit"
          disabled={isSubmitDisabled()}
        />
      );
    }
  };

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
      {getPromptInputButton()}
    </form>
  );
};

export default PromptInput;
