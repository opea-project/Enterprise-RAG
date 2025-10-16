// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./GeneratedSummary.scss";

import {
  CopyButton,
  LoadingFallback,
} from "@intel-enterprise-rag-ui/components";

interface GeneratedSummaryProps {
  summary?: string;
  isLoading?: boolean;
}

const GeneratedSummary = ({ summary, isLoading }: GeneratedSummaryProps) => {
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
    <div className="generated-summary">
      <p>Summary</p>
      {getContent()}
    </div>
  );
};

export default GeneratedSummary;
