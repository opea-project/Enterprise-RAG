// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ActionDialog,
  addNotification,
} from "@intel-enterprise-rag-ui/components";
import { useLocation, useNavigate } from "react-router-dom";

import { paths } from "@/config/paths";
import {
  useDeleteChatMutation,
  useLazyGetAllChatsQuery,
} from "@/features/chat/api/chatHistory";
import { ChatItemData } from "@/features/chat/types/api";
import { useAppDispatch } from "@/store/hooks";

interface DeleteChatDialogProps {
  itemData: ChatItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const DeleteChatDialog = ({
  itemData: { id },
  isOpen,
  onOpenChange,
}: DeleteChatDialogProps) => {
  const [deleteChat] = useDeleteChatMutation();
  const [getAllChats] = useLazyGetAllChatsQuery();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();

  const handleDeleteConfirm = () => {
    deleteChat({ id })
      .unwrap()
      .catch((error) => {
        dispatch(
          addNotification({
            severity: "error",
            text: `Failed to delete chat history: ${error.message}`,
          }),
        );
      })
      .then(() => {
        getAllChats();
        if (location.pathname === `${paths.chat}/${id}`) {
          navigate(paths.chat);
        }
      });
  };

  return (
    <ActionDialog
      title="Delete Chat"
      confirmLabel="Delete"
      confirmColor="error"
      isOpen={isOpen}
      onConfirm={handleDeleteConfirm}
      onOpenChange={onOpenChange}
    >
      <p className="text-xs">
        Are you sure you want to delete this chat?
        <br /> This action cannot be undone.
      </p>
    </ActionDialog>
  );
};

export default DeleteChatDialog;
