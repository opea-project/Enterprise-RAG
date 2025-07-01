// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionTab.scss";

import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import {
  useLazyGetFilesQuery,
  useLazyGetLinksQuery,
  useLazyGetS3BucketsListQuery,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import BucketSynchronizationDialog from "@/features/admin-panel/data-ingestion/components/BucketSynchronizationDialog/BucketSynchronizationDialog";
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

  const isFetchingData =
    isGetFilesQueryFetching ||
    isGetLinksQueryFetching ||
    isGetS3BucketsListQueryFetching;

  const refreshData = () => {
    Promise.all([
      getFiles().refetch(),
      getLinks().refetch(),
      getS3BucketsList().refetch(),
    ]);
  };

  const tooltipTitle = isFetchingData ? "Fetching data..." : "Refresh Data";
  const icon = isFetchingData ? "loading" : "refresh";

  const handlePress = () => {
    if (!isFetchingData) {
      refreshData();
    }
  };

  return (
    <Tooltip
      title={tooltipTitle}
      trigger={
        <IconButton
          isDisabled={isFetchingData}
          icon={icon}
          onPress={handlePress}
        />
      }
    />
  );
};

const DataIngestionTab = () => (
  <div className="data-ingestion-panel">
    <S3CertificateAlertBanner />
    <header>
      <h2>Stored Data</h2>
      <div className="data-ingestion-panel__actions">
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
