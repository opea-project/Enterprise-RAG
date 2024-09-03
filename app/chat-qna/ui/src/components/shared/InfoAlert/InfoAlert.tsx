// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./InfoAlert.scss";

import { Alert, Button } from "@mui/material";
import { PropsWithChildren, useState } from "react";

interface InfoAlertProps extends PropsWithChildren {
  localStorageShowKey: string;
}

const InfoAlert = ({ localStorageShowKey, children }: InfoAlertProps) => {
  const initialShowInfoAlert = JSON.parse(
    localStorage.getItem(localStorageShowKey) ?? "true",
  );
  const [showInfoAlert, setShowInfoAlert] = useState(initialShowInfoAlert);

  const handleAlertClose = () => {
    setShowInfoAlert(() => false);
    localStorage.setItem(localStorageShowKey, "false");
  };

  const handleShowInfoTextButtonClick = () => {
    setShowInfoAlert(() => true);
    localStorage.setItem(localStorageShowKey, "true");
  };

  return showInfoAlert ? (
    <Alert severity="info" className="info-alert" onClose={handleAlertClose}>
      {children}
    </Alert>
  ) : (
    <Button
      variant="text"
      onClick={handleShowInfoTextButtonClick}
      className="show-info-alert-button"
    >
      Show Info
    </Button>
  );
};

export default InfoAlert;
