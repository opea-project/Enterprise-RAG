// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadDataDialog.scss";

import {
  addNotification,
  Dialog,
  DialogRef,
  IconButton,
  Label,
  SelectInput,
  SelectInputChangeHandler,
  Tooltip,
} from "@intel-enterprise-rag-ui/components";
import { useMemo, useRef, useState } from "react";

import { useGetFilePresignedUrlMutation } from "@/api";
import {
  useGetS3BucketsListQuery,
  useGetSharePointSitesQuery,
  useLazyGetFilesQuery,
  useLazyGetLinksQuery,
  usePostLinksMutation,
  usePostSharePointUploadMutation,
} from "@/features/admin-panel/data-ingestion/api/edpApi";
import { usePostFileMutation } from "@/features/admin-panel/data-ingestion/api/s3Api";
import FilesIngestionPanel from "@/features/admin-panel/data-ingestion/components/FilesIngestionPanel/FilesIngestionPanel";
import LinksIngestionPanel from "@/features/admin-panel/data-ingestion/components/LinksIngestionPanel/LinksIngestionPanel";
import UploadDataDialogFooter from "@/features/admin-panel/data-ingestion/components/UploadDataDialogFooter/UploadDataDialogFooter";
import { ERROR_MESSAGES } from "@/features/admin-panel/data-ingestion/config/api";
import useIsSharePointEnabled from "@/features/admin-panel/data-ingestion/hooks/useIsSharePointEnabled";
import {
  LinkForIngestion,
  UploadErrors,
} from "@/features/admin-panel/data-ingestion/types";
import {
  createToBeUploadedMessage,
  isUploadDisabled,
} from "@/features/admin-panel/data-ingestion/utils";
import {
  S3_BUCKET_EMOJI,
  SHAREPOINT_SITE_EMOJI,
} from "@/features/admin-panel/utils";
import { useAppDispatch } from "@/store/hooks";
import { getErrorMessage } from "@/utils/api";

const initialUploadErrors = {
  files: "",
  links: "",
};

const UploadDataDialog = () => {
  const [getFiles] = useLazyGetFilesQuery();
  const [getLinks] = useLazyGetLinksQuery();
  const [getFilePresignedUrl] = useGetFilePresignedUrlMutation();
  const [postFile] = usePostFileMutation();
  const [postLinks] = usePostLinksMutation();
  const [postSharePointUpload] = usePostSharePointUploadMutation();

  const { data: bucketsList, isFetching: isFetchingBuckets } =
    useGetS3BucketsListQuery();
  const { data: spSites } = useGetSharePointSitesQuery();
  const isSharePointEnabled = useIsSharePointEnabled();
  const hasSites = isSharePointEnabled && spSites && spSites.length > 0;

  const [files, setFiles] = useState<File[]>([]);
  const [links, setLinks] = useState<LinkForIngestion[]>([]);
  const [selectedDestination, setSelectedDestination] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadErrors, setUploadErrors] =
    useState<UploadErrors>(initialUploadErrors);

  const dialogRef = useRef<DialogRef>(null);

  const dispatch = useAppDispatch();

  const destinationItems = useMemo(() => {
    const buckets = (bucketsList ?? []).map((b) => `${S3_BUCKET_EMOJI}${b}`);
    if (!hasSites) return buckets;
    const sites = spSites!.map(
      (s) => `${SHAREPOINT_SITE_EMOJI}${s.display_name || s.name}`,
    );
    return [...buckets, ...sites];
  }, [bucketsList, spSites, hasSites]);

  const effectiveBucket = useMemo(() => {
    if (!selectedDestination) return "";
    if (selectedDestination.startsWith(SHAREPOINT_SITE_EMOJI)) {
      return "";
    }
    return selectedDestination.slice(S3_BUCKET_EMOJI.length);
  }, [selectedDestination]);

  const selectedSharePointSiteId = useMemo(() => {
    if (!selectedDestination) return "";
    if (!selectedDestination.startsWith(SHAREPOINT_SITE_EMOJI)) return "";
    const siteName = selectedDestination.slice(SHAREPOINT_SITE_EMOJI.length);
    const site = spSites?.find((s) => (s.display_name || s.name) === siteName);
    return site?.id ?? "";
  }, [selectedDestination, spSites]);

  const isSharePointDestination = selectedSharePointSiteId !== "";

  const hasFileTarget = effectiveBucket !== "" || isSharePointDestination;

  const onDestinationChange: SelectInputChangeHandler<string> = (value) => {
    setSelectedDestination(value);
  };

  const resetUploadErrors = () => {
    setUploadErrors(initialUploadErrors);
  };

  const onDialogClose = () => {
    setFiles([]);
    setLinks([]);
    resetUploadErrors();
    dialogRef.current?.close();
  };

  const submitUploadData = async () => {
    resetUploadErrors();
    setIsUploading(true);

    let filesUploadError = "";
    let linksUploadError = "";

    if (files.length && hasFileTarget) {
      let error;

      if (isSharePointDestination) {
        // Upload files directly to SharePoint via the dedicated endpoint
        for (const file of files) {
          const { error: uploadError } = await postSharePointUpload({
            site_id: selectedSharePointSiteId,
            file,
          });

          if (uploadError) {
            error = uploadError;
            break;
          }
        }
      } else {
        // S3 bucket upload via presigned URL
        for (const file of files) {
          const { data: presignedUrl, error: getFilePresignedUrlError } =
            await getFilePresignedUrl({
              fileName: file.name,
              method: "PUT",
              bucketName: effectiveBucket,
            });

          if (getFilePresignedUrlError) {
            error = getFilePresignedUrlError;
            break;
          }

          if (presignedUrl) {
            const { error: postFileError } = await postFile({
              url: presignedUrl,
              file,
            });

            if (postFileError) {
              error = postFileError;
              break;
            }
          }
        }
      }

      if (error) {
        filesUploadError = getErrorMessage(error, ERROR_MESSAGES.POST_FILES);
      } else {
        setFiles([]);
      }
    }

    if (links.length) {
      const linksUrls = links.map(({ value }) => value);
      const { error } = await postLinks(linksUrls);

      if (error) {
        linksUploadError = getErrorMessage(error, ERROR_MESSAGES.POST_LINKS);
      } else {
        setLinks([]);
      }
    }

    if (filesUploadError || linksUploadError) {
      setUploadErrors({
        links: linksUploadError,
        files: filesUploadError,
      });
    } else {
      setUploadErrors(initialUploadErrors);
      onDialogClose();
      dispatch(
        addNotification({
          text: "Successful data upload!",
          severity: "success",
        }),
      );
      Promise.all([getFiles().refetch(), getLinks().refetch()]);
    }

    setIsUploading(false);
  };

  const toBeUploadedMessage = createToBeUploadedMessage(
    files,
    hasFileTarget ? "selected" : "",
    links,
  );

  const isSelectDisabled = isFetchingBuckets || destinationItems.length === 0;
  const isSelectInvalid = files.length > 0 && !selectedDestination;

  return (
    <Dialog
      ref={dialogRef}
      data-testid="upload-data-dialog"
      trigger={
        <Tooltip
          title="Upload Data"
          trigger={
            <IconButton
              data-testid="upload-data-trigger-button"
              icon="upload"
              variant="contained"
            />
          }
        />
      }
      footer={
        <UploadDataDialogFooter
          uploadErrors={uploadErrors}
          toBeUploadedMessage={toBeUploadedMessage}
          isUploadDisabled={isUploadDisabled(
            files,
            hasFileTarget ? "selected" : "",
            links,
            isUploading,
          )}
          isUploading={isUploading}
          onSubmit={submitUploadData}
        />
      }
      title="Upload Data"
      onClose={onDialogClose}
    >
      <div className="upload-dialog__content">
        <div className="px-4 pt-3">
          <Label>Upload to</Label>
          {hasSites && (
            <div className="text-light-text-primary dark:text-dark-text-primary flex gap-4 pt-1 text-xs">
              <span>{S3_BUCKET_EMOJI} S3 Bucket</span>
              <span>{SHAREPOINT_SITE_EMOJI} SharePoint Site</span>
            </div>
          )}
        </div>
        <SelectInput
          data-testid="destination-dropdown"
          value={selectedDestination || undefined}
          items={destinationItems}
          name="upload-destination"
          isDisabled={isSelectDisabled}
          isInvalid={isSelectInvalid}
          placeholder="Please select destination to upload files"
          className="px-4 pt-1"
          onChange={onDestinationChange}
        />
        <div className="upload-dialog__ingestion-panels-grid">
          <FilesIngestionPanel files={files} setFiles={setFiles} />
          <LinksIngestionPanel links={links} setLinks={setLinks} />
        </div>
        {isUploading && <div className="upload-dialog__blur-overlay"></div>}
      </div>
    </Dialog>
  );
};
export default UploadDataDialog;
