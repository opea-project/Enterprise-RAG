// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";

import Anchor from "@/components/ui/Anchor/Anchor";
import Button from "@/components/ui/Button/Button";
import {
  s3Api,
  selectS3Api,
} from "@/features/admin-panel/data-ingestion/api/s3Api";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const s3Url = import.meta.env.VITE_S3_URL;

const S3CertificateAlertBanner = () => {
  const [hasErrors, setHasErrors] = useState(false);

  const { queries, mutations } = useAppSelector(selectS3Api);
  const dispatch = useAppDispatch();

  const queriesErrors = Object.values(queries).map((query) => query?.error);
  const mutationsErrors = Object.values(mutations).map(
    (mutation) => mutation?.error,
  );
  const allErrors = [...queriesErrors, ...mutationsErrors].filter(
    (error) => error,
  );

  useEffect(() => {
    setHasErrors(allErrors.length > 0);
  }, [allErrors.length]);

  const handleS3UrlClick = () => {
    dispatch(s3Api.util.resetApiState());
  };

  const handleDismissBtnClick = () => {
    setHasErrors(false);
    dispatch(s3Api.util.resetApiState());
  };

  if (!hasErrors) {
    return null;
  }

  return (
    <div className="mb-4 rounded-md bg-light-status-error px-4 py-3 text-sm dark:bg-dark-status-error">
      <p className="text-light-text-inverse">
        It seems there was an error with your file action, possibly due to a
        self-signed certificate issue.
        <br /> Please click the link below to accept the certificate, then try
        the action again.
      </p>
      <Anchor
        href={s3Url}
        className="text-light-text-inverse"
        onClick={handleS3UrlClick}
      >
        {s3Url}
      </Anchor>
      <p className="my-2">
        If you believe this is a false positive, you can dismiss this alert
        using the button below.
      </p>
      <Button variant="outlined" size="sm" onClick={handleDismissBtnClick}>
        Dismiss
      </Button>
    </div>
  );
};

export default S3CertificateAlertBanner;
