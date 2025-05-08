// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import classNames from "classnames";
import { useEffect } from "react";
import { v4 as uuidv4 } from "uuid";

import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { useGetS3BucketsListQuery } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import { useAppDispatch } from "@/store/hooks";
import { getErrorMessage } from "@/utils/api";

interface BucketsDropdownProps {
  selectedBucket: string;
  files: File[];
  onBucketChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
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

  const selectClassNames = classNames([
    "mb-2",
    {
      "input--invalid": files.length > 0 && selectedBucket === "",
    },
  ]);

  const isDisabled = isFetching || !bucketsList || bucketsList.length === 0;

  return (
    <div className="px-4 pt-3">
      <label htmlFor="buckets-select" className="w-full">
        S3 Bucket
      </label>
      <select
        id="buckets-select"
        name="buckets-select"
        value={selectedBucket}
        disabled={isDisabled}
        className={selectClassNames}
        onChange={onBucketChange}
      >
        <option value=""> Please select bucket to upload files </option>
        {bucketsList?.map((bucket) => (
          <option key={uuidv4()} value={bucket}>
            {bucket}
          </option>
        ))}
      </select>
    </div>
  );
};

export default BucketsDropdown;
