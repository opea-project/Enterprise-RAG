// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { usePostFileToExtractTextMutation } from "@/features/admin-panel/data-ingestion/api/edpApi";
import TextExtractionDialog from "@/features/admin-panel/data-ingestion/components/debug/TextExtractionDialog/TextExtractionDialog";
import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import useTextExtraction from "@/features/admin-panel/data-ingestion/hooks/debug/useTextExtraction";

interface FileTextExtractionDialogProps {
  uuid: string;
  fileName: string;
}

const FileTextExtractionDialog = ({
  uuid,
  fileName,
}: FileTextExtractionDialogProps) => {
  const {
    extractedText,
    isLoading,
    errorMessage,
    onTriggerPress,
    onFormSubmit,
  } = useTextExtraction(
    usePostFileToExtractTextMutation,
    ERROR_MESSAGES.POST_FILE_TO_EXTRACT_TEXT,
    uuid,
  );

  return (
    <TextExtractionDialog
      objectName={fileName}
      extractedText={extractedText}
      isLoading={isLoading}
      errorMessage={errorMessage}
      onFormSubmit={onFormSubmit}
      onTriggerPress={onTriggerPress}
    />
  );
};

export default FileTextExtractionDialog;
