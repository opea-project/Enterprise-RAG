// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  addNotification,
  SelectInput,
  SelectInputChangeHandler,
} from "@intel-enterprise-rag-ui/components";
import { useEffect } from "react";

import { useGetS3BucketsListQuery } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import { useAppDispatch } from "@/store/hooks";
import { getErrorMessage } from "@/utils/api";

interface BucketsDropdownProps {
  selectedBucket: string;
  files: File[];
  onBucketChange: SelectInputChangeHandler<string>;
}

const BucketsDropdown = ({
  selectedBucket,
  files,
  onBucketChange,
}: BucketsDropdownProps) => {
  const { data: bucketsList, error, isFetching } = useGetS3BucketsListQuery();
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (error) {
      const errorMessage = getErrorMessage(
        error,
        ERROR_MESSAGES.GET_S3_BUCKETS_LIST,
      );
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    }
  }, [dispatch, error]);

  const isInvalid = files.length > 0 && !selectedBucket;
  const isDisabled = isFetching || !bucketsList || bucketsList.length === 0;

  return (
    <SelectInput
      value={selectedBucket}
      items={bucketsList}
      name="s3-bucket"
      label="S3 Bucket"
      isDisabled={isDisabled}
      isInvalid={isInvalid}
      placeholder="Please select bucket to upload files"
      className="px-4 pt-3"
      onChange={onBucketChange}
    />
  );
};

export default BucketsDropdown;
