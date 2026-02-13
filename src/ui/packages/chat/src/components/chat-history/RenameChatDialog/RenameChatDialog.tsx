// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./RenameChatDialog.scss";

import { ActionDialog, TextInput } from "@intel-enterprise-rag-ui/components";
import { ChangeEvent, useEffect, useRef, useState } from "react";

const CHAT_NAME_CHAR_LIMIT = 250;

export type OnRenameChatHandler = (chatId: string, newName: string) => void;

interface RenameChatDialogProps {
  chatId: string;
  currentName: string;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onRename: OnRenameChatHandler;
}

export const RenameChatDialog = ({
  chatId,
  currentName,
  isOpen,
  onOpenChange,
  onRename,
}: RenameChatDialogProps) => {
  const textInputRef = useRef<HTMLInputElement>(null);
  const [newChatName, setNewChatName] = useState(currentName);

  useEffect(() => {
    if (isOpen) {
      setNewChatName(currentName.slice(0, CHAT_NAME_CHAR_LIMIT));
      textInputRef.current?.focus();
    }
  }, [isOpen, currentName]);

  const handleChatNameChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.value.length <= CHAT_NAME_CHAR_LIMIT) {
      setNewChatName(event.target.value);
    } else {
      setNewChatName(event.target.value.slice(0, CHAT_NAME_CHAR_LIMIT));
    }
  };

  const handleRenameConfirm = () => {
    const trimmedName = newChatName.trim();
    onRename(chatId, trimmedName);
    setNewChatName(trimmedName);
    onOpenChange(false);
  };

  const handleCloseDialog = () => {
    setNewChatName(currentName);
  };

  const isRenameActionDisabled =
    !newChatName.trim() || newChatName === currentName;

  return (
    <ActionDialog
      title="Rename Chat"
      isConfirmDisabled={isRenameActionDisabled}
      isOpen={isOpen}
      onConfirm={handleRenameConfirm}
      onCancel={handleCloseDialog}
      onOpenChange={onOpenChange}
    >
      <TextInput
        ref={textInputRef}
        name="new-chat-name"
        value={newChatName}
        size="sm"
        label="Chat Name"
        onChange={handleChatNameChange}
      />
      <p className="rename-chat-dialog__char-count">
        {newChatName.length} / {CHAT_NAME_CHAR_LIMIT} characters
      </p>
    </ActionDialog>
  );
};
