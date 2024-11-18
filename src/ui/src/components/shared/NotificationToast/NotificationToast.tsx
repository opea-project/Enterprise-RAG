// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NotificationToast.scss";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { BsCheck2, BsXLg } from "react-icons/bs";

type NotificationSeverity = "success" | "error";

export interface Notification {
  open: boolean;
  message: string;
  severity: NotificationSeverity;
}

interface NotificationToastProps extends Notification {
  hideNotification: () => void;
}

const NotificationToast = ({
  open,
  message,
  severity,
  hideNotification,
}: NotificationToastProps) => {
  useEffect(() => {
    if (open) {
      setTimeout(() => {
        hideNotification();
      }, 5000);
    }
  }, [hideNotification, open]);

  return open
    ? createPortal(
        <div className={`notification-snackbar notification-${severity}`}>
          {severity === "success" && <BsCheck2 size={24} />}
          {severity === "error" && <BsXLg size={16} />}
          {message}
        </div>,
        document.body,
      )
    : null;
};

export default NotificationToast;
