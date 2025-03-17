// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { getS3BucketsList } from "@/features/admin-panel/data-ingestion/api/getS3BucketsList";
import { useAppDispatch } from "@/store/hooks";

interface BucketsDropdownProps {
  selectedBucket: string;
  onBucketChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
}

const BucketsDropdown = ({
  selectedBucket,
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

  return (
    <>
      <label htmlFor="buckets-select" className="w-full">
        S3 Bucket
      </label>
      <select
        id="buckets-select"
        name="buckets-select"
        value={selectedBucket}
        disabled={isDropdownDisabled}
        className="mb-2"
        onChange={onBucketChange}
      >
        <option value=""> Please select bucket </option>
        {bucketsList.map((bucket) => (
          <option key={uuidv4()} value={bucket}>
            {bucket}
          </option>
        ))}
      </select>
    </>
  );
};

export default BucketsDropdown;
