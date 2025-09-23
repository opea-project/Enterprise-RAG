// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { usePostLinkToExtractTextMutation } from "@/features/admin-panel/data-ingestion/api/edpApi";
import TextExtractionDialog from "@/features/admin-panel/data-ingestion/components/debug/TextExtractionDialog/TextExtractionDialog";
import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import useTextExtraction from "@/features/admin-panel/data-ingestion/hooks/debug/useTextExtraction";

interface LinkTextExtractionDialogProps {
  uuid: string;
  linkUri: string;
}

const LinkTextExtractionDialog = ({
  uuid,
  linkUri,
}: LinkTextExtractionDialogProps) => {
  const {
    extractedText,
    isLoading,
    errorMessage,
    onTriggerPress,
    onFormSubmit,
  } = useTextExtraction(
    usePostLinkToExtractTextMutation,
    ERROR_MESSAGES.POST_LINK_TO_EXTRACT_TEXT,
    uuid,
  );

  return (
    <TextExtractionDialog
      objectName={linkUri}
      extractedText={extractedText}
      isLoading={isLoading}
      errorMessage={errorMessage}
      onFormSubmit={onFormSubmit}
      onTriggerPress={onTriggerPress}
    />
  );
};

export default LinkTextExtractionDialog;
