// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Anchor, Button } from "@intel-enterprise-rag-ui/components";
import { useEffect, useState } from "react";

import { appApi, selectAppApi } from "@/api";
import {
  s3Api,
  selectS3Api,
} from "@/features/admin-panel/data-ingestion/api/s3Api";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { getChatQnAAppEnv } from "@/utils";

const s3Url = getChatQnAAppEnv("S3_URL");

const isFetchError = (error: unknown) =>
  typeof error === "object" &&
  error !== null &&
  "status" in error &&
  (error as { status: unknown }).status === "FETCH_ERROR";

const S3CertificateAlertBanner = () => {
  const [hasErrors, setHasErrors] = useState(false);

  const s3ApiState = useAppSelector(selectS3Api);
  const appApiState = useAppSelector(selectAppApi);
  const dispatch = useAppDispatch();

  const s3Errors = [
    ...Object.values(s3ApiState.queries).map((q) => q?.error),
    ...Object.values(s3ApiState.mutations).map((m) => m?.error),
  ];
  const appErrors = [
    ...Object.values(appApiState.queries).map((q) => q?.error),
    ...Object.values(appApiState.mutations).map((m) => m?.error),
  ];
  const allFetchErrors = [...s3Errors, ...appErrors].filter(isFetchError);

  useEffect(() => {
    setHasErrors(allFetchErrors.length > 0);
  }, [allFetchErrors.length]);

  const handleS3UrlPress = () => {
    dispatch(s3Api.util.resetApiState());
    dispatch(appApi.util.resetApiState());
  };

  const handleDismissBtnPress = () => {
    setHasErrors(false);
    dispatch(s3Api.util.resetApiState());
    dispatch(appApi.util.resetApiState());
  };

  if (!hasErrors) {
    return null;
  }

  return (
    <div className="bg-light-status-error dark:bg-dark-status-error mb-4 rounded-md px-4 py-3 text-sm">
      <p className="text-light-text-inverse">
        It seems there was an error with your file action, possibly due to a
        self-signed certificate issue.
        <br /> Please click the link below to accept the certificate, then try
        the action again.
      </p>
      <Anchor
        data-testid="s3-certificate-link"
        href={s3Url}
        className="text-light-text-inverse"
        onPress={handleS3UrlPress}
      >
        {s3Url}
      </Anchor>
      <p className="my-2">
        If you believe this is a false positive, you can dismiss this alert
        using the button below.
      </p>
      <Button
        data-testid="dismiss-s3-certificate-alert-button"
        variant="outlined"
        size="sm"
        onPress={handleDismissBtnPress}
      >
        Dismiss
      </Button>
    </div>
  );
};

export default S3CertificateAlertBanner;
