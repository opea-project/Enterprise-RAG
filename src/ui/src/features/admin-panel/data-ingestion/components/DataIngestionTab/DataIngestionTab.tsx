// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionTab.scss";

import Button from "@/components/ui/Button/Button";
import {
  useLazyGetFilesQuery,
  useLazyGetLinksQuery,
  useLazyGetS3BucketsListQuery,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import FilesDataTable from "@/features/admin-panel/data-ingestion/components/FilesDataTable/FilesDataTable";
import LinksDataTable from "@/features/admin-panel/data-ingestion/components/LinksDataTable/LinksDataTable";
import S3CertificateAlertBanner from "@/features/admin-panel/data-ingestion/components/S3CertificateAlertBanner/S3CertificateAlertBanner";
import UploadDataDialog from "@/features/admin-panel/data-ingestion/components/UploadDataDialog/UploadDataDialog";

const RefreshButton = () => {
  const [getFiles, { isFetching: isGetFilesQueryFetching }] =
    useLazyGetFilesQuery();
  const [getLinks, { isFetching: isGetLinksQueryFetching }] =
    useLazyGetLinksQuery();
  const [getS3BucketsList, { isFetching: isGetS3BucketsListQueryFetching }] =
    useLazyGetS3BucketsListQuery();

  const refreshData = () => {
    Promise.all([
      getFiles().refetch(),
      getLinks().refetch(),
      getS3BucketsList().refetch(),
    ]);
  };

  const isDisabled =
    isGetFilesQueryFetching ||
    isGetLinksQueryFetching ||
    isGetS3BucketsListQueryFetching;

  return (
    <Button
      variant="outlined"
      icon="refresh"
      isDisabled={isDisabled}
      onPress={refreshData}
    >
      Refresh
    </Button>
  );
};

const DataIngestionTab = () => (
  <div className="data-ingestion-panel">
    <S3CertificateAlertBanner />
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
