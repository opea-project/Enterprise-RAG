// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NotificationToast.scss";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { BsCheck2, BsXLg } from "react-icons/bs";

import { setNotification } from "@/store/dataIngestion.slice";
import { useAppDispatch } from "@/store/hooks";
import { NOTIFICATION_DISPLAY_TIME } from "@/utils/notifications";

type NotificationSeverity = "success" | "error";

export interface Notification {
  open: boolean;
  message: string;
  severity: NotificationSeverity;
}

type NotificationToastProps = Notification;

const NotificationToast = ({
  open,
  message,
  severity,
}: NotificationToastProps) => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (open) {
      setTimeout(() => {
        dispatch(
          setNotification({
            open: false,
            message: "",
            severity: "success",
          }),
        );
      }, NOTIFICATION_DISPLAY_TIME);
    }
  }, [dispatch, open]);

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
