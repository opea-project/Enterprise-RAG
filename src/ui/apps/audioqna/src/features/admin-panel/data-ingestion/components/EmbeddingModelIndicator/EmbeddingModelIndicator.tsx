// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/**
 * EmbeddingModelIndicator component
 *
 * Displays a warning icon for files and links that need re-ingestion due to embedding model changes.
 *
 * Environment variables:
 * - EMBEDDING_MODEL_MIGRATION_REQUIRED: "true" if migration is enabled
 * - EMBEDDING_MODEL_MIGRATION_NEW_MODEL: Current embedding model used by the system
 * - EMBEDDING_MODEL_MIGRATION_OLD_MODEL: Previous embedding model (for reference)
 *
 * Note: Despite the name "NEW_MODEL", this variable holds the CURRENT model in use.
 * Files with a different embedding_model value need to be re-ingested.
 */

import { Tooltip } from "@intel-enterprise-rag-ui/components";
import { WarningIcon } from "@intel-enterprise-rag-ui/icons";

import { getAudioQnAAppEnv } from "@/utils";

interface EmbeddingModelIndicatorProps {
  //  please use itemEmbeddingModel isntead of fileEmbeddingModel.
  itemEmbeddingModel: string | null;
}

const EmbeddingModelIndicator = ({
  itemEmbeddingModel,
}: EmbeddingModelIndicatorProps) => {
  const currentEmbeddingModel = getAudioQnAAppEnv(
    "EMBEDDING_MODEL_MIGRATION_NEW_MODEL",
  );
  const migrationRequired =
    getAudioQnAAppEnv("EMBEDDING_MODEL_MIGRATION_REQUIRED") === "true";

  if (!migrationRequired) {
    return null;
  }

  if (!currentEmbeddingModel) {
    return null;
  }

  if (itemEmbeddingModel === currentEmbeddingModel) {
    return null;
  }

  // Show indicator for items with:
  // - NULL embedding_model (old items from before migration feature), OR
  // - Different embedding model than current

  const indicator = (
    <span
      className="mr-2 inline-flex cursor-help items-center justify-center text-amber-600 dark:text-amber-400"
      aria-label="Re-ingestion Required"
    >
      <WarningIcon className="h-4 w-4" />
    </span>
  );

  const tooltipContent = (
    <div className="text-sm">
      <p className="mb-1 font-semibold">Re-ingestion Required</p>
      <p className="mb-1">
        This item uses an outdated embedding model and needs to be re-ingested.
      </p>
      <p className="text-xs">
        Current model:{" "}
        <span className="font-mono">{itemEmbeddingModel || "unknown"}</span>
      </p>
      <p className="text-xs">
        Expected model:{" "}
        <span className="font-mono">{currentEmbeddingModel}</span>
      </p>
      <p className="mt-2 text-xs opacity-80">
        Use the &quot;Reingest&quot; action to update it.
      </p>
    </div>
  );

  return (
    <Tooltip title={tooltipContent} trigger={indicator} placement="right" />
  );
};

export default EmbeddingModelIndicator;
