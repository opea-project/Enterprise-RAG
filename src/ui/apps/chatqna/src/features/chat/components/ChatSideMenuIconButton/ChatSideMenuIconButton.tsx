// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SideMenuIconButton } from "@intel-enterprise-rag-ui/layouts";

import {
  selectIsChatHistorySideMenuOpen,
  toggleChatHistorySideMenu,
} from "@/features/chat/store/chatSideMenus.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const ChatSideMenuIconButton = () => {
  const isChatHistorySideMenuOpen = useAppSelector(
    selectIsChatHistorySideMenuOpen,
  );

  const dispatch = useAppDispatch();

  const handlePress = () => {
    dispatch(toggleChatHistorySideMenu());
  };

  return (
    <SideMenuIconButton
      isSideMenuOpen={isChatHistorySideMenuOpen}
      onPress={handlePress}
    />
  );
};

export default ChatSideMenuIconButton;
