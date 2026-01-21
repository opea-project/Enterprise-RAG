// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinksDataTable.scss";

import { DataTable, SearchBar } from "@intel-enterprise-rag-ui/components";
import { useCallback, useMemo, useState } from "react";

import {
  useDeleteLinkMutation,
  useGetLinksQuery,
  useRetryLinkActionMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import useConditionalPolling from "@/features/admin-panel/data-ingestion/hooks/useConditionalPolling";
import { getLinksTableColumns } from "@/features/admin-panel/data-ingestion/utils/data-tables/links";

const LinksDataTable = () => {
  const { data: links, refetch, isLoading } = useGetLinksQuery();
  useConditionalPolling(links, refetch);

  const [deleteLink] = useDeleteLinkMutation();
  const [retryLinkAction] = useRetryLinkActionMutation();
  const [filter, setFilter] = useState("");

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

  const defaultData = links || [];

  const linksTableColumns = useMemo(
    () =>
      getLinksTableColumns({
        retryHandler,
        deleteHandler,
      }),
    [retryHandler, deleteHandler],
  );

  return (
    <div className="flex flex-col gap-2">
      <SearchBar
        value={filter}
        placeholder="Filter links by status or link"
        onChange={setFilter}
      />
      <DataTable
        defaultData={defaultData}
        columns={linksTableColumns}
        isDataLoading={isLoading}
        globalFilter={filter}
        className="links-data-table"
      />
    </div>
  );
};

export default LinksDataTable;
