// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInput.scss";

import {
  ChangeEventHandler,
  FormEventHandler,
  KeyboardEventHandler,
  useEffect,
  useRef,
  useState,
} from "react";

import PromptInputButton from "@/components/chat/PromptInputButton/PromptInputButton";
import {
  addNewBotMessage,
  addNewUserMessage,
  postPrompt,
  selectAbortController,
  selectIsStreaming,
} from "@/store/conversationFeed.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

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

  const submitPrompt = async () => {
    dispatch(addNewUserMessage(prompt));
    dispatch(addNewBotMessage());
    dispatch(postPrompt(prompt));

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
      if (prompt.trim() !== "" && !isStreaming) {
        submitPrompt();
      }
    }
  };

  const getPromptInputButton = () => {
    if (isStreaming) {
      const stopStreaming = () => {
        if (abortController) {
          abortController.abort(""); // empty string set for further error handling
        }
      };

      const handleStopBtnClick = () => {
        stopStreaming();
      };

      const handleStopBtnKeyDown: KeyboardEventHandler = (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          stopStreaming();
          focusPromptInput();
        }
      };

      return (
        <PromptInputButton
          icon="mdi:stop"
          type="button"
          onClick={handleStopBtnClick}
          onKeyDown={handleStopBtnKeyDown}
        />
      );
    } else {
      const submitBtnDisabled = prompt === "";

      return (
        <PromptInputButton
          icon="tabler:arrow-up"
          type="submit"
          disabled={submitBtnDisabled}
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
        onChange={handleChange}
        onKeyDown={handleKeyDown}
      />
      {getPromptInputButton()}
    </form>
  );
};

export default PromptInput;
