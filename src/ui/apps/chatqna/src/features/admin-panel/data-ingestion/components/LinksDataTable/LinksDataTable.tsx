// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DataTable } from "@intel-enterprise-rag-ui/components";
import { useCallback, useMemo } from "react";

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
    () => getLinksTableColumns({ retryHandler, deleteHandler }),
    [retryHandler, deleteHandler],
  );

  return (
    <DataTable
      defaultData={defaultData}
      columns={linksTableColumns}
      isDataLoading={isLoading}
    />
  );
};

export default LinksDataTable;
