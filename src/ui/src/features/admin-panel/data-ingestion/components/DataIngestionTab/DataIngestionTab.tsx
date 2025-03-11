// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionTab.scss";

import Button from "@/components/ui/Button/Button";
import FilesDataTable from "@/features/admin-panel/data-ingestion/components/FilesDataTable/FilesDataTable";
import LinksDataTable from "@/features/admin-panel/data-ingestion/components/LinksDataTable/LinksDataTable";
import UploadDataDialog from "@/features/admin-panel/data-ingestion/components/UploadDataDialog/UploadDataDialog";
import {
  fetchFiles,
  fetchLinks,
  filesDataIsLoadingSelector,
} from "@/features/admin-panel/data-ingestion/store/dataIngestion.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const RefreshButton = () => {
  const filesDataIsLoading = useAppSelector(filesDataIsLoadingSelector);
  const dispatch = useAppDispatch();
  const refreshData = () => {
    dispatch(fetchFiles());
    dispatch(fetchLinks());
  };

  return (
    <Button
      variant="outlined"
      icon="refresh"
      disabled={filesDataIsLoading}
      onClick={refreshData}
    >
      Refresh
    </Button>
  );
};

const DataIngestionTab = () => (
  <div className="data-ingestion-panel">
    <header>
      <h2>Stored Data</h2>
      <div className="data-ingestion-panel__actions">
        <RefreshButton />
        <UploadDataDialog />
      </div>
    </header>
    <section className="mb-4">
      <h3>Files</h3>
      <FilesDataTable />
    </section>
    <section className="mb-4">
      <h3>Links</h3>
      <LinksDataTable />
    </section>
  </div>
);

export default DataIngestionTab;
