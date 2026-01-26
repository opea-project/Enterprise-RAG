// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SideMenuIconButton } from "@intel-enterprise-rag-ui/layouts";

interface ChatSideMenuIconButtonProps {
  isOpen: boolean;
  onPress: () => void;
}

export const ChatSideMenuIconButton = ({
  isOpen,
  onPress,
}: ChatSideMenuIconButtonProps) => (
  <SideMenuIconButton isSideMenuOpen={isOpen} onPress={onPress} />
);
