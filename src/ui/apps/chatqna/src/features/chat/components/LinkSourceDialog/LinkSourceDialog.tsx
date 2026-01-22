// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LinkIcon } from "@intel-enterprise-rag-ui/icons";

import SourceDialog from "@/features/chat/components/SourceDialog/SourceDialog";
import { LinkSource } from "@/features/chat/types";

interface LinkSourceDialogProps {
  source: LinkSource;
}

const LinkSourceDialog = ({
  source: { url, citations },
}: LinkSourceDialogProps) => {
  const handleOpenLink = () => {
    window.open(url, "_blank");
  };

  return (
    <SourceDialog
      name={url}
      triggerIcon={<LinkIcon />}
      actionLabel="Open Link"
      citations={citations}
      onAction={handleOpenLink}
    />
  );
};

export default LinkSourceDialog;
