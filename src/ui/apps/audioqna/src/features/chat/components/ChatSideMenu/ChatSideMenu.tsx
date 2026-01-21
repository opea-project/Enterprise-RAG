// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SideMenu } from "@intel-enterprise-rag-ui/layouts";

import ChatHistoryList from "@/features/chat/components/ChatHistoryList/ChatHistoryList";
import { selectIsChatHistorySideMenuOpen } from "@/features/chat/store/chatSideMenus.slice";
import { useAppSelector } from "@/store/hooks";

const ChatSideMenu = () => {
  const isChatHistorySideMenuOpen = useAppSelector(
    selectIsChatHistorySideMenuOpen,
  );

  return (
    <SideMenu
      direction="left"
      isOpen={isChatHistorySideMenuOpen}
      ariaLabel="Chat Side Menu"
    >
      <ChatHistoryList />
    </SideMenu>
  );
};

export default ChatSideMenu;
