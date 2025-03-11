// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import DataTable from "@/components/ui/DataTable/DataTable";
import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { deleteLink } from "@/features/admin-panel/data-ingestion/api/deleteLink";
import { retryLinkAction } from "@/features/admin-panel/data-ingestion/api/retryLinkAction";
import {
  fetchLinks,
  linksDataIsLoadingSelector,
  linksDataSelector,
} from "@/features/admin-panel/data-ingestion/store/dataIngestion.slice";
import { getLinksTableColumns } from "@/features/admin-panel/data-ingestion/utils/data-tables/links";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const LinksDataTable = () => {
  const linksData = useAppSelector(linksDataSelector);
  const linksDataIsLoading = useAppSelector(linksDataIsLoadingSelector);
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(fetchLinks());
  }, []);

  const deleteHandler = async (uuid: string) => {
    try {
      await deleteLink(uuid);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete link";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    } finally {
      dispatch(fetchLinks());
    }
  };

  const retryHandler = async (uuid: string) => {
    try {
      await retryLinkAction(uuid);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to retry link action";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    } finally {
      dispatch(fetchLinks());
    }
  };

  const linksTableColumns = getLinksTableColumns({
    retryHandler,
    deleteHandler,
  });

  return (
    <DataTable
      defaultData={linksData}
      columns={linksTableColumns}
      isDataLoading={linksDataIsLoading}
    />
  );
};

export default LinksDataTable;
