// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import DataTable from "@/components/shared/DataTable/DataTable";
import DataIngestionService from "@/services/dataIngestionService";
import {
  getLinks,
  linksDataIsLoadingSelector,
  linksDataSelector,
} from "@/store/dataIngestion.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { addNotification } from "@/store/notifications.slice";
import { getLinksTableColumns } from "@/utils/data-ingestion/dataTableColumns";

const LinksDataTable = () => {
  const linksData = useAppSelector(linksDataSelector);
  const linksDataIsLoading = useAppSelector(linksDataIsLoadingSelector);
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(getLinks());
  }, []);

  const deleteLink = async (uuid: string) => {
    try {
      await DataIngestionService.deleteLink(uuid);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete link";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    } finally {
      dispatch(getLinks());
    }
  };

  const retryLinkAction = async (uuid: string) => {
    try {
      await DataIngestionService.retryLinkAction(uuid);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to retry link action";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    } finally {
      dispatch(getLinks());
    }
  };

  const linksTableColumns = getLinksTableColumns({
    retryHandler: retryLinkAction,
    deleteHandler: deleteLink,
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
