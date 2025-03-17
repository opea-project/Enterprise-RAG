// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./InitialChatLayout.scss";

import { ChangeEventHandler } from "react";

import ChatBotIcon from "@/components/icons/ChatBotIcon/ChatBotIcon";
import PromptInput from "@/components/ui/PromptInput/PromptInput";
import ChatDisclaimer from "@/features/chat/components/ChatDisclaimer/ChatDisclaimer";
import {
  addNewBotMessage,
  addNewUserMessage,
  selectPrompt,
  sendPrompt,
  setPrompt,
} from "@/features/chat/store/conversationFeed.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";

const InitialChatLayout = () => {
  const prompt = useAppSelector(selectPrompt);
  const dispatch = useAppDispatch();

  const onPromptSubmit = () => {
    const sanitizedPrompt = sanitizeString(prompt);
    dispatch(addNewUserMessage(sanitizedPrompt));
    dispatch(addNewBotMessage());
    dispatch(sendPrompt(sanitizedPrompt));
    dispatch(setPrompt(""));
  };

  const onPromptChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    dispatch(setPrompt(event.target.value));
  };

  return (
    <div className="initial-chat-layout">
      <ChatBotIcon />
      <p className="initial-chat-layout__greeting">What do you want to know?</p>
      <PromptInput
        prompt={prompt}
        onChange={onPromptChange}
        onSubmit={onPromptSubmit}
      />
      <ChatDisclaimer />
    </div>
  );
};

export default InitialChatLayout;
