// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconButton, Tooltip } from "@intel-enterprise-rag-ui/components";

import {
  useLazyGetFilesQuery,
  useLazyGetLinksQuery,
  useLazyGetS3BucketsListQuery,
} from "@/features/admin-panel/data-ingestion/api/edpApi";

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

export default RefreshButton;
