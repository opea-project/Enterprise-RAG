// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatPage.scss";

import ConversationFeed from "@/components/chat/ConversationFeed/ConversationFeed";
import PromptInput from "@/components/chat/PromptInput/PromptInput";

const ChatPage = () => (
  <div className="chat-page">
    <ConversationFeed />
    <PromptInput />
  </div>
);

export default ChatPage;
