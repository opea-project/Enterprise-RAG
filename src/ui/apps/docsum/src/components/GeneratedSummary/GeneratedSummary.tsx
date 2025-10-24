// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./GeneratedSummary.scss";

import {
  CopyButton,
  LoadingFallback,
} from "@intel-enterprise-rag-ui/components";
import { useState } from "react";

import ExportActionDialog from "@/components/ExportActionDialog/ExportActionDialog";
import ExportButton from "@/components/ExportButton/ExportButton";

interface GeneratedSummaryProps {
  summary?: string;
  isLoading?: boolean;
  fileName?: string;
}

const GeneratedSummary = ({
  summary,
  isLoading,
  fileName,
}: GeneratedSummaryProps) => {
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const getContent = () => {
    if (isLoading) {
      return (
        <div className="generated-summary__loading">
          <LoadingFallback loadingMessage="Generating your summary..." />
        </div>
      );
    }

    if (!summary) {
      return (
        <p className="generated-summary__no-summary">
          Your summary will be displayed here
        </p>
      );
    }

    return (
      <div className="generated-summary__result">
        <p>{summary}</p>
        <span className="copy-btn-wrapper">
          <CopyButton textToCopy={summary} />
        </span>
      </div>
    );
  };

  return (
    <>
      <div className="generated-summary">
        <div className="generated-summary__header">
          <p>Summary</p>
          {summary && fileName && (
            <ExportButton onPress={() => setIsExportDialogOpen(true)} />
          )}
        </div>
        {getContent()}
      </div>
      {summary && fileName && (
        <ExportActionDialog
          summary={summary}
          fileName={fileName}
          isOpen={isExportDialogOpen}
          onOpenChange={setIsExportDialogOpen}
        />
      )}
    </>
  );
};

export default GeneratedSummary;
