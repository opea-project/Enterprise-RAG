// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./BucketSynchronizationDialog.scss";

import { useMemo, useRef, useState } from "react";

import { IconName } from "@/components/icons";
import Button from "@/components/ui/Button/Button";
import CheckboxInput from "@/components/ui/CheckboxInput/CheckboxInput";
import DataTable from "@/components/ui/DataTable/DataTable";
import Dialog, { DialogRef } from "@/components/ui/Dialog/Dialog";
import IconButton from "@/components/ui/IconButton/IconButton";
import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import {
  useLazyGetFilesQuery,
  useLazyGetFilesSyncQuery,
  usePostFilesSyncMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import { filesSyncColumns } from "@/features/admin-panel/data-ingestion/utils/data-tables/filesSync";
import { useAppDispatch } from "@/store/hooks";

interface BucketSynchronizationDialogFooterProps {
  hasActionableFiles: boolean;
  onSuccessfulSynchronization: () => void;
}

const BucketSynchronizationDialogFooter = ({
  hasActionableFiles,
  onSuccessfulSynchronization,
}: BucketSynchronizationDialogFooterProps) => {
  const [postFilesSync, { error: postFilesSyncError, isLoading }] =
    usePostFilesSyncMutation();

  const btnContent = isLoading ? "Synchronizing..." : "Synchronize";
  const btnIcon: IconName | undefined = isLoading ? "loading" : undefined;

  const handleSynchronizeBtnPress = async () => {
    const { error } = await postFilesSync();

    if (!error) {
      onSuccessfulSynchronization();
    }
  };

  const isSyncActionDisabled = !hasActionableFiles || isLoading;

  return (
    <footer className="bucket-synchronization-dialog__footer">
      {!hasActionableFiles && <p>Manual synchronization is not required</p>}
      {postFilesSyncError && (
        <p className="error">{ERROR_MESSAGES.POST_FILES_SYNC}</p>
      )}
      <Button
        icon={btnIcon}
        isDisabled={isSyncActionDisabled}
        onPress={handleSynchronizeBtnPress}
      >
        {btnContent}
      </Button>
    </footer>
  );
};

const BucketSynchronizationDialog = () => {
  const [showAllFiles, setShowAllFiles] = useState(false);

  const [
    getFilesSync,
    {
      currentData: getFilesSyncData,
      isFetching: isFetchingFilesSync,
      error: getFilesSyncError,
    },
  ] = useLazyGetFilesSyncQuery();
  const [getFiles] = useLazyGetFilesQuery();

  const dispatch = useAppDispatch();

  const dialogRef = useRef<DialogRef>(null);

  const onSuccessfulSynchronization = () => {
    dialogRef.current?.close();
    dispatch(
      addNotification({
        text: "Successful bucket synchronization!",
        severity: "success",
      }),
    );
    getFiles();
  };

  const filesSyncTableData = useMemo(() => {
    if (!getFilesSyncData) return [];
    return showAllFiles
      ? getFilesSyncData
      : getFilesSyncData.filter((item) => !item.action.includes("no action"));
  }, [getFilesSyncData, showAllFiles]);

  const hasActionableFiles = useMemo(
    () =>
      filesSyncTableData.some((item) =>
        ["add", "delete", "update"].includes(item.action),
      ),
    [filesSyncTableData],
  );

  const dialogTrigger = useMemo(() => {
    const handleDialogTriggerPress = () => {
      getFilesSync();
    };

    return (
      <Tooltip
        title="Synchronize Buckets"
        trigger={
          <IconButton
            variant="outlined"
            icon="bucket-synchronization"
            onPress={handleDialogTriggerPress}
          />
        }
      />
    );
  }, [getFilesSync]);

  const dialogContent = useMemo(() => {
    const handleShowAllFilesCheckboxChange = () =>
      setShowAllFiles((prevValue) => !prevValue);

    return getFilesSyncError ? (
      <p className="error">{ERROR_MESSAGES.GET_FILES_SYNC}</p>
    ) : (
      <>
        <CheckboxInput
          label="Show all files"
          size="sm"
          name="show-all-items"
          isSelected={showAllFiles}
          onChange={handleShowAllFilesCheckboxChange}
        />
        <DataTable
          defaultData={filesSyncTableData}
          columns={filesSyncColumns}
          isDataLoading={isFetchingFilesSync}
          dense
        />
      </>
    );
  }, [
    getFilesSyncError,
    showAllFiles,
    filesSyncTableData,
    isFetchingFilesSync,
  ]);

  return (
    <Dialog
      ref={dialogRef}
      trigger={dialogTrigger}
      title="Bucket Synchronization"
      footer={
        <BucketSynchronizationDialogFooter
          hasActionableFiles={hasActionableFiles}
          onSuccessfulSynchronization={onSuccessfulSynchronization}
        />
      }
    >
      <div className="bucket-synchronization-dialog__content">
        <p className="mb-4">
          Below you can see files that need actions to be synchronized inside S3
          buckets.
          <br />
          Click "Synchronize" button to perform additions and deletions of
          actionable files listed below.
        </p>
        {dialogContent}
      </div>
    </Dialog>
  );
};

export default BucketSynchronizationDialog;
