// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/**
 * EmbeddingModelMigrationBanner component
 *
 * Displays a banner when files/links need re-ingestion due to embedding model changes.
 * Shows progress, estimated time, and allows manual refresh.
 *
 * Environment variables:
 * - EMBEDDING_MODEL_MIGRATION_REQUIRED: "true" to enable migration tracking
 * - EMBEDDING_MODEL_MIGRATION_NEW_MODEL: Current embedding model in the system
 * - EMBEDDING_MODEL_MIGRATION_OLD_MODEL: Previous embedding model (for display purposes)
 *
 * Important: EMBEDDING_MODEL_MIGRATION_NEW_MODEL should be set to the CURRENT model
 * that the system is using. Files with different models will show as needing migration.
 */

import { Button } from "@intel-enterprise-rag-ui/components";
import { RefreshIcon, WarningIcon } from "@intel-enterprise-rag-ui/icons";
import { useMemo, useState } from "react";

import {
  useGetFilesQuery,
  useGetLinksQuery,
  useRetryFileActionMutation,
  useRetryLinkActionMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import { getAudioQnAAppEnv } from "@/utils";

const EmbeddingModelMigrationBanner = () => {
  const migrationRequired =
    getAudioQnAAppEnv("EMBEDDING_MODEL_MIGRATION_REQUIRED") === "true";
  const oldModel = getAudioQnAAppEnv("EMBEDDING_MODEL_MIGRATION_OLD_MODEL");
  const newModel = getAudioQnAAppEnv("EMBEDDING_MODEL_MIGRATION_NEW_MODEL");

  const {
    data: files,
    isLoading: filesLoading,
    refetch: refetchFiles,
    isFetching: filesFetching,
  } = useGetFilesQuery(undefined, {
    skip: !migrationRequired,
    pollingInterval: 30000, // Poll every 30 seconds to track progress
  });

  const {
    data: links,
    isLoading: linksLoading,
    refetch: refetchLinks,
    isFetching: linksFetching,
  } = useGetLinksQuery(undefined, {
    skip: !migrationRequired,
    pollingInterval: 30000,
  });

  const isLoading = filesLoading || linksLoading;
  const isFetching = filesFetching || linksFetching;

  const [retryFileAction] = useRetryFileActionMutation();
  const [retryLinkAction] = useRetryLinkActionMutation();
  const [isReingesting, setIsReingesting] = useState(false);

  const refetch = () => {
    refetchFiles();
    refetchLinks();
  };

  const handleReingestAll = async () => {
    if (isReingesting) return;

    setIsReingesting(true);
    try {
      // Get all items needing migration
      const fileItems = (files || []).filter(
        (file) => file.embedding_model !== newModel,
      );
      const linkItems = (links || []).filter(
        (link) => link.embedding_model !== newModel,
      );

      // Reingest all files
      for (const file of fileItems) {
        try {
          await retryFileAction(file.id).unwrap();
        } catch (error) {
          console.error(`Failed to reingest file ${file.id}:`, error);
        }
      }

      // Reingest all links
      for (const link of linkItems) {
        try {
          await retryLinkAction(link.id).unwrap();
        } catch (error) {
          console.error(`Failed to reingest link ${link.id}:`, error);
        }
      }

      // Refresh data after reingestion
      refetch();
    } finally {
      setIsReingesting(false);
    }
  };

  const fileStats = useMemo(() => {
    if (!newModel) {
      return { total: 0, oldFiles: 0 };
    }

    // Combine files and links into one array for unified processing
    const allItems = [...(files || []), ...(links || [])];

    const total = allItems.length;

    // Items with old model, different model, OR NULL (need re-ingestion)
    const oldFiles = allItems.filter(
      (item) => item.embedding_model !== newModel,
    ).length;

    return { total, oldFiles };
  }, [files, links, newModel]);

  // Don't show banner if:
  // - Migration not required, OR
  // - No files/links exist yet (fresh installation), OR
  // - All files have been re-ingested (no old files remaining)
  if (!migrationRequired || fileStats.total === 0 || fileStats.oldFiles === 0) {
    return null;
  }

  if (isLoading) {
    return null; // Don't show loading state, just wait
  }

  return (
    <div className="bg-light-bg-2 dark:bg-dark-bg-2 border-light-border dark:border-dark-border mb-4 rounded-md border px-4 py-3 text-sm">
      <div className="flex items-start gap-3">
        <WarningIcon className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
        <div className="flex-1">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="font-semibold">
              Action Required: Embedding Model Changed
            </h3>
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="hover:bg-light-background-secondary dark:hover:bg-dark-background-secondary ml-2 rounded p-1.5 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
              title="Refresh migration status"
              aria-label="Refresh migration status"
            >
              <RefreshIcon
                className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`}
              />
            </button>
          </div>
          <p className="mb-2">
            The embedding model has been changed from{" "}
            <span className="font-semibold">{oldModel}</span> to{" "}
            <span className="font-semibold">{newModel}</span>. As a result,
            previously indexed documents are no longer compatible with the new
            embedding space and must be re-ingested to restore full search
            quality and availability.
          </p>

          {fileStats.total > 0 && fileStats.oldFiles > 0 && (
            <>
              <p className="mb-3 font-medium">
                Documents needed to be re-ingested:{" "}
                <strong>{fileStats.oldFiles}</strong>
              </p>
              <Button
                size="sm"
                onPress={handleReingestAll}
                isDisabled={isReingesting}
              >
                {isReingesting ? "Reingesting..." : "Reingest All"}
              </Button>
              <p className="mt-3 text-left text-xs opacity-80">
                This banner will automatically disappear once all documents have
                been re-ingested.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmbeddingModelMigrationBanner;
