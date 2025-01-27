// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionTab.scss";

import { MdRefresh } from "react-icons/md";

import FilesDataTable from "@/components/admin-panel/data-ingestion/FilesDataTable/FilesDataTable";
import LinksDataTable from "@/components/admin-panel/data-ingestion/LinksDataTable/LinksDataTable";
import UploadDataDialog from "@/components/admin-panel/data-ingestion/UploadDataDialog/UploadDataDialog";
import { getFiles, getLinks } from "@/store/dataIngestion.slice";
import { useAppDispatch } from "@/store/hooks";

const RefreshButton = () => {
  const dispatch = useAppDispatch();
  const refreshData = () => {
    dispatch(getFiles());
    dispatch(getLinks());
  };

  return (
    <button
      className="refresh-btn outlined-button--primary"
      onClick={refreshData}
    >
      <MdRefresh fontSize={20} /> Refresh
    </button>
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
    <section>
      <h3>Files</h3>
      <FilesDataTable />
    </section>
    <section>
      <h3>Links</h3>
      <LinksDataTable />
    </section>
  </div>
);

export default DataIngestionTab;
