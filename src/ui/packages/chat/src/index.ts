// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Components
export { ChatSideMenu } from "@/components/chat-history/ChatSideMenu/ChatSideMenu";
export { ChatSideMenuIconButton } from "@/components/chat-history/ChatSideMenuIconButton/ChatSideMenuIconButton";
export { ConversationFeed } from "@/components/conversation-feed/ConversationFeed/ConversationFeed";
export { NewChatButton } from "@/components/conversation-feed/NewChatButton/NewChatButton";
export { PromptInput } from "@/components/conversation-feed/PromptInput/PromptInput";

// Layouts
export { ChatConversationLayout } from "@/layouts/ChatConversationLayout/ChatConversationLayout";
export { InitialChatLayout } from "@/layouts/InitialChatLayout/InitialChatLayout";

// Types
export type { ChatTurn } from "@/types";

// API Factories
export { createChatHistoryApi } from "@/api/chatHistory.api";
export { createQnAApi, type QnAApiConfig } from "@/api/qna.api";

// Store - Redux Slices
export {
  chatHistoryReducer,
  resetChatHistorySlice,
  setChatTurns,
} from "@/store/chatHistory.slice";
export {
  chatSideMenuReducer,
  resetChatSideMenuSlice,
  selectIsChatSideMenuOpen,
  toggleChatSideMenu,
} from "@/store/chatSideMenu.slice";

// Hooks
export { useChat } from "@/hooks/useChat";
export { useChatHistoryHandlers } from "@/hooks/useChatHistoryHandlers";
export { useInitialChat } from "@/hooks/useInitialChat";
