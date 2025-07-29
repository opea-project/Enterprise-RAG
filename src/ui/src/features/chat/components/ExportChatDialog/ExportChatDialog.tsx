// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ActionDialog from "@/components/ui/ActionDialog/ActionDialog";
import { useLazyGetChatByIdQuery } from "@/features/chat/api/chatHistory";
import { ChatItemData } from "@/features/chat/types/api";
import { downloadBlob } from "@/utils";

interface ExportChatDialogProps {
  itemData: ChatItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const ExportChatDialog = ({
  itemData: { id, name },
  isOpen,
  onOpenChange,
}: ExportChatDialogProps) => {
  const [getChatById] = useLazyGetChatByIdQuery();

  const handleExportConfirm = () => {
    getChatById({ id })
      .unwrap()
      .then((response) => {
        if (response.history) {
          const itemBlob = new Blob(
            [JSON.stringify(response.history, null, 2)],
            {
              type: "application/json",
            },
          );
          downloadBlob(itemBlob, name + ".json");
        }
      });
  };

  return (
    <ActionDialog
      title="Export Chat"
      confirmLabel="Export"
      onConfirm={handleExportConfirm}
      isOpen={isOpen}
      onOpenChange={onOpenChange}
    >
      <p className="text-xs">
        Exported file will contain conversation in a JSON format.
      </p>
    </ActionDialog>
  );
};

export default ExportChatDialog;
