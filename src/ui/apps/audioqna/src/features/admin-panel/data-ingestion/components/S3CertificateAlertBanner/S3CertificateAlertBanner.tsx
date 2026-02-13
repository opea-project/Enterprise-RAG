// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Anchor, Button } from "@intel-enterprise-rag-ui/components";
import { useEffect, useState } from "react";

import {
  s3Api,
  selectS3Api,
} from "@/features/admin-panel/data-ingestion/api/s3Api";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { getChatQnAAppEnv } from "@/utils";

const s3Url = getChatQnAAppEnv("S3_URL");

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

  const handleS3UrlPress = () => {
    dispatch(s3Api.util.resetApiState());
  };

  const handleDismissBtnPress = () => {
    setHasErrors(false);
    dispatch(s3Api.util.resetApiState());
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
      <Button variant="outlined" size="sm" onPress={handleDismissBtnPress}>
        Dismiss
      </Button>
    </div>
  );
};

export default S3CertificateAlertBanner;
