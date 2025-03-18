// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import classNames from "classnames";
import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { getS3BucketsList } from "@/features/admin-panel/data-ingestion/api/getS3BucketsList";
import { useAppDispatch } from "@/store/hooks";

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
  const [bucketsList, setBucketsList] = useState<string[]>(["default"]);
  const [isDropdownDisabled, setIsDropdownDisabled] = useState(false);

  const dispatch = useAppDispatch();

  useEffect(() => {
    const fetchBucketsList = async () => {
      const response = await getS3BucketsList();
      setBucketsList(response);
    };

    setIsDropdownDisabled(true);
    try {
      fetchBucketsList();
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to fetch S3 buckets list";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    } finally {
      setIsDropdownDisabled(false);
    }
  }, [dispatch]);

  const selectClassNames = classNames([
    "mb-2",
    {
      "input--invalid": files.length > 0 && selectedBucket === "",
    },
  ]);

  return (
    <div className="px-4 pt-3">
      <label htmlFor="buckets-select" className="w-full">
        S3 Bucket
      </label>
      <select
        id="buckets-select"
        name="buckets-select"
        value={selectedBucket}
        disabled={isDropdownDisabled}
        className={selectClassNames}
        onChange={onBucketChange}
      >
        <option value=""> Please select bucket to upload files </option>
        {bucketsList.map((bucket) => (
          <option key={uuidv4()} value={bucket}>
            {bucket}
          </option>
        ))}
      </select>
    </div>
  );
};

export default BucketsDropdown;
