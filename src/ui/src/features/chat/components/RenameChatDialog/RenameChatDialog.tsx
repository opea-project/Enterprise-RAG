// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEvent, useEffect, useRef, useState } from "react";

import ActionDialog from "@/components/ui/ActionDialog/ActionDialog";
import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import TextInput from "@/components/ui/TextInput/TextInput";
import { useChangeChatNameMutation } from "@/features/chat/api/chatHistory";
import { ChatItemData } from "@/features/chat/types/api";
import { useAppDispatch } from "@/store/hooks";

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
      setNewChatName(name);
      textInputRef.current?.focus();
    }
  }, [isOpen, name]);

  const dispatch = useAppDispatch();

  const handleChatNameChange = (event: ChangeEvent<HTMLInputElement>) => {
    setNewChatName(event.target.value);
  };

  const isRenameActionDisabled = !newChatName.trim() || newChatName === name;

  const handleRenameConfirm = () => {
    changeChatName({
      id,
      newName: newChatName.trim(),
    })
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

  return (
    <ActionDialog
      title="Rename Chat"
      isConfirmDisabled={isRenameActionDisabled}
      onConfirm={handleRenameConfirm}
      onCancel={handleCloseDialog}
      isOpen={isOpen}
      onOpenChange={onOpenChange}
    >
      <TextInput
        ref={textInputRef}
        name="chat-entry-name"
        value={newChatName}
        size="sm"
        label="Chat Name"
        onChange={handleChatNameChange}
      />
    </ActionDialog>
  );
};

export default RenameChatDialog;
