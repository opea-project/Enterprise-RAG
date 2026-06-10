// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinksDataTable.scss";

import {
  DataTable,
  RowSelectionState,
  SearchBar,
} from "@intel-enterprise-rag-ui/components";
import { useCallback, useMemo, useState } from "react";

import {
  useDeleteLinkMutation,
  useGetLinksQuery,
  useRetryLinkActionMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import BatchActionsDropdown from "@/features/admin-panel/data-ingestion/components/BatchActionsDropdown/BatchActionsDropdown";
import BatchDeleteDialog from "@/features/admin-panel/data-ingestion/components/BatchDeleteDialog/BatchDeleteDialog";
import useConditionalPolling from "@/features/admin-panel/data-ingestion/hooks/useConditionalPolling";
import { LinkDataItem } from "@/features/admin-panel/data-ingestion/types";
import { getLinksTableColumns } from "@/features/admin-panel/data-ingestion/utils/data-tables/links";
import { getChatQnAAppEnv } from "@/utils";

const LinksDataTable = () => {
  const { data: links, refetch, isLoading } = useGetLinksQuery();
  useConditionalPolling(links, refetch);

  const [deleteLink] = useDeleteLinkMutation();
  const [retryLinkAction] = useRetryLinkActionMutation();
  const [filter, setFilter] = useState("");
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const retryHandler = useCallback(
    (uuid: string) => {
      retryLinkAction(uuid);
    },
    [retryLinkAction],
  );

  const deleteHandler = useCallback(
    (uuid: string) => {
      deleteLink(uuid);
    },
    [deleteLink],
  );

  const defaultData = useMemo(() => {
    return links || [];
  }, [links]);

  const linksTableColumns = useMemo(
    () =>
      getLinksTableColumns({
        retryHandler,
        deleteHandler,
      }),
    [retryHandler, deleteHandler],
  );

  const selectedLinks = useMemo(() => {
    return Object.keys(rowSelection)
      .map((id) => defaultData.find((link) => link.id === id))
      .filter((link): link is LinkDataItem => link !== undefined);
  }, [rowSelection, defaultData]);

  const retryableLinks = useMemo(() => {
    return selectedLinks.filter((link) => link.status === "error");
  }, [selectedLinks]);

  const reingestableLinks = useMemo(() => {
    const currentEmbeddingModel = getChatQnAAppEnv(
      "EMBEDDING_MODEL_MIGRATION_NEW_MODEL",
    );
    if (!currentEmbeddingModel) return [];
    return selectedLinks.filter(
      (link) =>
        link.embedding_model !== currentEmbeddingModel &&
        link.status === "ingested",
    );
  }, [selectedLinks]);

  const handleBatchRetry = useCallback(async () => {
    await Promise.all(retryableLinks.map((link) => retryLinkAction(link.id)));
    setRowSelection({});
  }, [retryableLinks, retryLinkAction]);

  const handleBatchReingest = useCallback(async () => {
    await Promise.all(
      reingestableLinks.map((link) => retryLinkAction(link.id)),
    );
    setRowSelection({});
  }, [reingestableLinks, retryLinkAction]);

  const handleBatchDelete = useCallback(async () => {
    await Promise.all(selectedLinks.map((link) => deleteLink(link.id)));
    setRowSelection({});
  }, [selectedLinks, deleteLink]);

  const selectedLinkNames = useMemo(() => {
    return selectedLinks.map((link) => link.uri);
  }, [selectedLinks]);

  const getRowId = useCallback((row: LinkDataItem) => row.id, []);

  return (
    <div className="links-data-table-wrapper">
      <div className="links-data-table-wrapper__header">
        <SearchBar
          data-testid="links-search-bar"
          value={filter}
          placeholder="Filter links by status or link"
          onChange={setFilter}
        />
        <BatchActionsDropdown
          selectedCount={selectedLinks.length}
          retryableCount={retryableLinks.length}
          reingestableCount={reingestableLinks.length}
          onRetry={handleBatchRetry}
          onReingest={handleBatchReingest}
          onDelete={() => setIsDeleteDialogOpen(true)}
        />
      </div>
      <DataTable
        defaultData={defaultData}
        columns={linksTableColumns}
        isDataLoading={isLoading}
        globalFilter={filter}
        className="links-data-table"
        rowSelection={rowSelection}
        onRowSelectionChange={setRowSelection}
        getRowId={getRowId}
        enableRowSelection
      />
      <BatchDeleteDialog
        isOpen={isDeleteDialogOpen}
        itemType="links"
        itemNames={selectedLinkNames}
        onConfirm={handleBatchDelete}
        onClose={() => setIsDeleteDialogOpen(false)}
      />
    </div>
  );
};

export default LinksDataTable;
