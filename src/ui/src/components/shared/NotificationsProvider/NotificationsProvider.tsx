// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NotificationsProvider.scss";

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

import ErrorIcon from "@/components/icons/ErrorIcon/ErrorIcon";
import SuccessIcon from "@/components/icons/SuccessIcon/SuccessIcon";
import IconButton from "@/components/shared/IconButton/IconButton";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import {
  deleteNotification,
  Notification,
  notificationsSelector,
} from "@/store/notifications.slice";
import { NOTIFICATION_DISPLAY_TIME } from "@/utils/notifications";

type NotificationToastProps = Notification;

const NotificationToast = ({ id, text, severity }: NotificationToastProps) => {
  const dispatch = useAppDispatch();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    timeoutRef.current = setTimeout(() => {
      dispatch(deleteNotification(id));
    }, NOTIFICATION_DISPLAY_TIME);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [dispatch, id]);

  const handleClickDismissBtn = () => {
    dispatch(deleteNotification(id));
  };

  const icon = severity === "error" ? <ErrorIcon /> : <SuccessIcon />;

  return (
    <div className={`notification-toast notification-toast--${severity}`}>
      {icon}
      <span>{text}</span>
      <IconButton
        size="sm"
        icon="close-notification"
        className="notification-toast__dismiss-btn"
        onClick={handleClickDismissBtn}
      />
    </div>
  );
};

const NotificationsProvider = () => {
  const notifications = useAppSelector(notificationsSelector);

  if (notifications.length === 0) {
    return null;
  }

  return createPortal(
    <div className="notifications-provider">
      {notifications.map((notification) => (
        <NotificationToast key={notification.id} {...notification} />
      ))}
    </div>,
    document.body,
  );
};

export default NotificationsProvider;
