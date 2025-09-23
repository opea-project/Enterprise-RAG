// Copyright (C) 2024-2025 Intel Corporation
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

import PromptInputButton from "@/components/PromptInputButton/PromptInputButton";
import { promptMaxHeight, promptMaxLength } from "@/config/promptInput";

interface PromptInputProps {
  prompt: string;
  isChatResponsePending?: boolean;
  onRequestAbort?: () => void;
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  onSubmit: (prompt: string) => void;
}

const PromptInput = ({
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
    <form className="prompt-input__form" onSubmit={handleSubmit}>
      <AriaTextField className="pt-1.5" aria-label="Your message">
        <AriaTextArea
          ref={promptInputRef}
          value={prompt}
          name="prompt-input"
          placeholder="Enter your prompt..."
          maxLength={promptMaxLength}
          rows={1}
          className="prompt-input"
          onChange={onChange}
          onKeyDown={handleKeyDown}
        />
      </AriaTextField>
      {showStopButton && (
        <PromptInputButton
          icon="prompt-stop"
          type="button"
          aria-label="Stop response"
          onPress={handleStopBtnPress}
          onKeyDown={handleStopBtnKeyDown}
        />
      )}
      {showSendButton && (
        <PromptInputButton
          icon="prompt-send"
          type="submit"
          aria-label="Send prompt"
          isDisabled={isSubmitDisabled()}
        />
      )}
    </form>
  );
};

export default PromptInput;
