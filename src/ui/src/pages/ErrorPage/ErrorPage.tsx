// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ErrorPage.scss";

import { useEffect } from "react";
import { isRouteErrorResponse, useRouteError } from "react-router-dom";

const ErrorPage = () => {
  useEffect(() => {
    const theme = localStorage.getItem("theme");
    if (theme === "dark") {
      document.body.classList.add("dark");
    }
  }, []);

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
    <div className="error-page">
      {errorMessage}
      <a href="/chat">Return to the app</a>
    </div>
  );
};

export default ErrorPage;
