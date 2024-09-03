// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NotificationSnackbar.scss";

import { Alert, Snackbar } from "@mui/material";
import { AlertColor } from "@mui/material/Alert/Alert";

export interface AppNotification {
  open: boolean;
  message: string;
  severity: AlertColor;
}

interface NotificationSnackbarProps extends AppNotification {
  onNotificationClose: () => void;
}

const NotificationSnackbar = ({
  open,
  message,
  severity,
  onNotificationClose,
}: NotificationSnackbarProps) => (
  <Snackbar
    open={open}
    onClose={onNotificationClose}
    anchorOrigin={{ vertical: "top", horizontal: "right" }}
    autoHideDuration={6000}
    className="notification-snackbar"
  >
    <Alert severity={severity} variant="filled">
      {message}
    </Alert>
  </Snackbar>
);

export default NotificationSnackbar;
