// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionTab.scss";

import BucketSynchronizationDialog from "@/features/admin-panel/data-ingestion/components/BucketSynchronizationDialog/BucketSynchronizationDialog";
import DataIngestionSettingsDialog from "@/features/admin-panel/data-ingestion/components/DataIngestionSettingsDialog/DataIngestionSettingsDialog";
import FilesDataTable from "@/features/admin-panel/data-ingestion/components/FilesDataTable/FilesDataTable";
import LinksDataTable from "@/features/admin-panel/data-ingestion/components/LinksDataTable/LinksDataTable";
import RefreshButton from "@/features/admin-panel/data-ingestion/components/RefreshButton/RefreshButton";
import S3CertificateAlertBanner from "@/features/admin-panel/data-ingestion/components/S3CertificateAlertBanner/S3CertificateAlertBanner";
import UploadDataDialog from "@/features/admin-panel/data-ingestion/components/UploadDataDialog/UploadDataDialog";

const DataIngestionTab = () => (
  <div className="data-ingestion-tab">
    <S3CertificateAlertBanner />
    <header>
      <h2>Stored Data</h2>
      <div className="data-ingestion-tab__actions">
        <DataIngestionSettingsDialog />
        <RefreshButton />
        <BucketSynchronizationDialog />
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
