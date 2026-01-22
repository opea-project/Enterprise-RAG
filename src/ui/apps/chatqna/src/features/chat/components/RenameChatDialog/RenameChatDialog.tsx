// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ActionDialog,
  addNotification,
  TextInput,
} from "@intel-enterprise-rag-ui/components";
import { ChangeEvent, useEffect, useRef, useState } from "react";

import { useChangeChatNameMutation } from "@/features/chat/api/chatHistory";
import { ChatItemData } from "@/features/chat/types/api";
import { useAppDispatch } from "@/store/hooks";

const CHAT_NAME_CHAR_LIMIT = 250;

interface RenameChatDialogProps {
  itemData: ChatItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const RenameChatDialog = ({
  itemData: { name, id },
  isOpen,
  onOpenChange,
}: RenameChatDialogProps) => {
  const textInputRef = useRef<HTMLInputElement>(null);
  const [changeChatName] = useChangeChatNameMutation();
  const [newChatName, setNewChatName] = useState(name);

  useEffect(() => {
    if (isOpen) {
      setNewChatName(name.slice(0, CHAT_NAME_CHAR_LIMIT));
      textInputRef.current?.focus();
    }
  }, [isOpen, name]);

  const dispatch = useAppDispatch();

  const handleChatNameChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.value.length <= CHAT_NAME_CHAR_LIMIT) {
      setNewChatName(event.target.value);
    } else {
      setNewChatName(event.target.value.slice(0, CHAT_NAME_CHAR_LIMIT));
    }
  };

  const handleRenameConfirm = () => {
    changeChatName({ id, newName: newChatName.trim() })
      .unwrap()
      .then(() => {
        onOpenChange(false);
      })
      .catch((error) => {
        dispatch(
          addNotification({
            severity: "error",
            text: `Failed to rename chat: ${error.message}`,
          }),
        );
      });

    setNewChatName(newChatName.trim());
  };

  const handleCloseDialog = () => {
    setNewChatName(name);
  };

  const isRenameActionDisabled = !newChatName.trim() || newChatName === name;

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
      <p className="text-right text-xs">
        {newChatName.length} / {CHAT_NAME_CHAR_LIMIT} characters
      </p>
    </ActionDialog>
  );
};

export default RenameChatDialog;
