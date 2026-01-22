// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./GeneratedSummary.scss";

import {
  CopyButton,
  LoadingFallback,
} from "@intel-enterprise-rag-ui/components";
import { Markdown } from "@intel-enterprise-rag-ui/markdown";
import { useState } from "react";

import ExportActionDialog from "@/features/docsum/components/shared/ExportActionDialog/ExportActionDialog";
import ExportButton from "@/features/docsum/components/shared/ExportButton/ExportButton";

interface GeneratedSummaryProps {
  summary?: string;
  isLoading?: boolean;
  fileName?: string;
  data?: { text?: string };
  streamingText?: string;
}

const GeneratedSummary = ({
  summary,
  isLoading,
  fileName,
  streamingText,
}: GeneratedSummaryProps) => {
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);

  // Computed visibility states
  const isStreaming =
    isLoading &&
    streamingText !== undefined &&
    streamingText !== "" &&
    !summary;
  const displaySummary = isStreaming ? streamingText : summary;
  const hasContent = displaySummary !== undefined && displaySummary !== "";

  const showLoadingIndicator = isLoading && !streamingText;
  const showEmptyState = !hasContent;
  const showCopyButton = hasContent && !isStreaming;
  const showExportButton = hasContent && fileName && !isStreaming;
  const showExportDialog = hasContent && fileName && !isStreaming;

  const getContent = () => {
    if (showLoadingIndicator) {
      return (
        <div className="generated-summary__loading">
          <LoadingFallback loadingMessage="Generating your summary..." />
        </div>
      );
    }

    if (showEmptyState) {
      return (
        <p className="generated-summary__no-summary">
          Your summary will be displayed here
        </p>
      );
    }

    return (
      <div className="generated-summary__result">
        <div className="generated-summary__content">
          <Markdown text={displaySummary ?? ""} />
        </div>
        {showCopyButton && (
          <span className="copy-btn-wrapper">
            <CopyButton textToCopy={displaySummary ?? ""} />
          </span>
        )}
      </div>
    );
  };

  return (
    <>
      <div className="generated-summary">
        <div className="generated-summary__header">
          <p>Summary</p>
          {showExportButton && (
            <ExportButton onPress={() => setIsExportDialogOpen(true)} />
          )}
        </div>
        {getContent()}
      </div>
      {showExportDialog && (
        <ExportActionDialog
          summary={displaySummary ?? ""}
          fileName={fileName}
          isOpen={isExportDialogOpen}
          onOpenChange={setIsExportDialogOpen}
        />
      )}
    </>
  );
};

export default GeneratedSummary;
