// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionTab.scss";

import FilesDataTable from "@/components/admin-panel/data-ingestion/FilesDataTable/FilesDataTable";
import LinksDataTable from "@/components/admin-panel/data-ingestion/LinksDataTable/LinksDataTable";
import UploadDataDialog from "@/components/admin-panel/data-ingestion/UploadDataDialog/UploadDataDialog";
import Button from "@/components/shared/Button/Button";
import {
  filesDataIsLoadingSelector,
  getFiles,
  getLinks,
} from "@/store/dataIngestion.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const RefreshButton = () => {
  const filesDataIsLoading = useAppSelector(filesDataIsLoadingSelector);
  const dispatch = useAppDispatch();
  const refreshData = () => {
    dispatch(getFiles());
    dispatch(getLinks());
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
