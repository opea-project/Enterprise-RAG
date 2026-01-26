// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInput.scss";

import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import {
  ChangeEventHandler,
  FormEventHandler,
  KeyboardEventHandler,
  useCallback,
  useEffect,
  useRef,
} from "react";
import {
  TextArea as AriaTextArea,
  TextField as AriaTextField,
} from "react-aria-components";

import { PromptInputButton } from "@/components/conversation-feed/PromptInputButton/PromptInputButton";

const MAX_REQUEST_BODY_SIZE = 1 * 1024 * 1024; // 1MB in bytes - restriction from nginx config
const REQUEST_BODY_FORMAT_OVERHEAD = '{ "text": "" }'.length;
const PROMPT_MAX_LENGTH = MAX_REQUEST_BODY_SIZE - REQUEST_BODY_FORMAT_OVERHEAD;
const PROMPT_MAX_HEIGHT = 15 * 16; // must be the same as max-height set for prompt-input css class

interface PromptInputProps {
  prompt: string;
  isChatResponsePending?: boolean;
  onRequestAbort?: () => void;
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  onSubmit: (prompt: string) => void;
}

export const PromptInput = ({
  prompt,
  isChatResponsePending = false,
  onRequestAbort,
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

      const maxHeight = PROMPT_MAX_HEIGHT;
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
    const isPromptMaxLengthExceeded =
      sanitizedPrompt.length > PROMPT_MAX_LENGTH;

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
      if (!isSubmitDisabled() && !isChatResponsePending) {
        submitPrompt();
      }
    }
  };

  const handleStopBtnPress = () => {
    onRequestAbort?.();
    focusPromptInput();
  };

  const handleStopBtnKeyDown: KeyboardEventHandler = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      onRequestAbort?.();
      focusPromptInput();
    }
  };

  const showStopButton = onRequestAbort && isChatResponsePending;
  const showSendButton = !showStopButton;

  return (
    <form
      className="prompt-input__form"
      onSubmit={handleSubmit}
      data-testid="prompt-input-form"
    >
      <AriaTextField
        className="prompt-input__text-field"
        aria-label="Your message"
      >
        <AriaTextArea
          ref={promptInputRef}
          value={prompt}
          name="prompt-input"
          placeholder="Enter your prompt..."
          maxLength={PROMPT_MAX_LENGTH}
          rows={1}
          className="prompt-input"
          data-testid="prompt-input-textarea"
          onChange={onChange}
          onKeyDown={handleKeyDown}
        />
      </AriaTextField>
      {showStopButton && (
        <PromptInputButton
          data-testid="prompt-stop-button"
          icon="prompt-stop"
          type="button"
          aria-label="Stop response"
          onPress={handleStopBtnPress}
          onKeyDown={handleStopBtnKeyDown}
        />
      )}
      {showSendButton && (
        <PromptInputButton
          data-testid="prompt-send-button"
          icon="prompt-send"
          type="submit"
          aria-label="Send prompt"
          isDisabled={isSubmitDisabled()}
        />
      )}
    </form>
  );
};
