// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionTab.scss";

import { InfoIcon } from "@intel-enterprise-rag-ui/icons";

import BucketSynchronizationDialog from "@/features/admin-panel/data-ingestion/components/BucketSynchronizationDialog/BucketSynchronizationDialog";
import DataIngestionSettingsDialog from "@/features/admin-panel/data-ingestion/components/DataIngestionSettingsDialog/DataIngestionSettingsDialog";
import FilesDataTable from "@/features/admin-panel/data-ingestion/components/FilesDataTable/FilesDataTable";
import LinksDataTable from "@/features/admin-panel/data-ingestion/components/LinksDataTable/LinksDataTable";
import RefreshButton from "@/features/admin-panel/data-ingestion/components/RefreshButton/RefreshButton";
import S3CertificateAlertBanner from "@/features/admin-panel/data-ingestion/components/S3CertificateAlertBanner/S3CertificateAlertBanner";
import SharePointSitesDialog from "@/features/admin-panel/data-ingestion/components/SharePointSitesDialog/SharePointSitesDialog";
import UploadDataDialog from "@/features/admin-panel/data-ingestion/components/UploadDataDialog/UploadDataDialog";
import useIsSharePointEnabled from "@/features/admin-panel/data-ingestion/hooks/useIsSharePointEnabled";

const DataIngestionTab = () => {
  const isSharePointEnabled = useIsSharePointEnabled();

  return (
    <div className="data-ingestion-tab">
      <div className="bg-light-bg-2 dark:bg-dark-bg-2 border-light-border dark:border-dark-border mb-4 flex items-start gap-3 rounded-md border px-4 py-3 text-sm">
        <InfoIcon className="text-light-accent dark:text-dark-accent mt-0.5 shrink-0 text-base" />
        <p className="text-light-text-primary dark:text-dark-text-primary">
          This interface is designed for lightweight administrative management:
          monitoring ingestion jobs, checking processing results, and adding
          small sample files or links when needed. For best performance and
          reliability, files should be uploaded directly to the configured
          storage endpoint (e.g., S3 bucket or SharePoint) rather than through
          the UI.
        </p>
      </div>
      <S3CertificateAlertBanner />
      <header>
        <h2>Stored Data</h2>
        <div className="data-ingestion-tab__actions">
          <DataIngestionSettingsDialog />
          <RefreshButton />
          <BucketSynchronizationDialog />
          {isSharePointEnabled && <SharePointSitesDialog />}
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
};

export default DataIngestionTab;
