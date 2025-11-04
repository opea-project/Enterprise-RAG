// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ErrorRoute.scss";

import { Anchor } from "@intel-enterprise-rag-ui/components";
import { isRouteErrorResponse, useRouteError } from "react-router-dom";

import { paths } from "@/config/paths";

const ErrorRoute = () => {
  const error = useRouteError();

  let errorMessage = <p className="error">An error occurred!</p>;
  if (isRouteErrorResponse(error)) {
    if (error.status === 404) {
      errorMessage = <p>404 - Page Not Found</p>;
    } else {
      errorMessage = (
        <p className="error">
          An error occurred! <br />
          Error Code: {error.status} <br />
          Error Message: {error.statusText}
        </p>
      );
    }
  }

  return (
    <div className="error-route__layout">
      {errorMessage}
      <Anchor href={paths.docsum} target="_self">
        Return to the app
      </Anchor>
    </div>
  );
};

export default ErrorRoute;
