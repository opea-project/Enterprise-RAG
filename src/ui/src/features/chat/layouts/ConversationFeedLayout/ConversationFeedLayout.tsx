// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ConversationFeedLayout.scss";

import { ChangeEventHandler } from "react";

import ConversationFeed from "@/components/ui/ConversationFeed/ConversationFeed";
import PromptInput from "@/components/ui/PromptInput/PromptInput";
import ChatDisclaimer from "@/features/chat/components/ChatDisclaimer/ChatDisclaimer";
import {
  addNewBotMessage,
  addNewUserMessage,
  selectMessages,
  selectPrompt,
  sendPrompt,
  setPrompt,
} from "@/features/chat/store/conversationFeed.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";

const ConversationFeedLayout = () => {
  const messages = useAppSelector(selectMessages);
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
    <div className="conversation-feed-layout">
      <ConversationFeed messages={messages} />
      <PromptInput
        prompt={prompt}
        onChange={onPromptChange}
        onSubmit={onPromptSubmit}
      />
      <ChatDisclaimer />
    </div>
  );
};

export default ConversationFeedLayout;
