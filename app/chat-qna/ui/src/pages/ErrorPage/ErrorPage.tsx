// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ErrorPage.scss";

import { Link as MuiLink, Typography } from "@mui/material";
import { isRouteErrorResponse, Link, useRouteError } from "react-router-dom";

const ErrorPage = () => {
  const error = useRouteError();

  let errorMessage = <Typography color="error">An error occurred!</Typography>;
  if (isRouteErrorResponse(error)) {
    if (error.status === 404) {
      errorMessage = <Typography>404 - Page Not Found</Typography>;
    } else {
      errorMessage = (
        <Typography color="error">
          An error occurred! <br />
          Error Code: {error.status} <br />
          Error Message: {error.statusText}
        </Typography>
      );
    }
  }

  return (
    <div className="error-page">
      {errorMessage}
      <Link to={"/chat"}>
        <MuiLink>
          <Typography>Return to the app</Typography>
        </MuiLink>
      </Link>
    </div>
  );
};

export default ErrorPage;
