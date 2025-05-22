// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Notifications.scss";

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

import ErrorIcon from "@/components/icons/ErrorIcon/ErrorIcon";
import SuccessIcon from "@/components/icons/SuccessIcon/SuccessIcon";
import IconButton from "@/components/ui/IconButton/IconButton";
import {
  deleteNotification,
  notificationsSelector,
} from "@/components/ui/Notifications/notifications.slice";
import { Notification } from "@/components/ui/Notifications/types";
import { notificationsConfig } from "@/config/notifications";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

type NotificationToastProps = Notification;

const NotificationToast = ({ id, text, severity }: NotificationToastProps) => {
  const dispatch = useAppDispatch();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    timeoutRef.current = setTimeout(() => {
      dispatch(deleteNotification(id));
    }, notificationsConfig.hideDelay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [dispatch, id]);

  const handleDismissBtnPress = () => {
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
        aria-label="Dismiss notification"
        className="notification-toast__dismiss-btn"
        onPress={handleDismissBtnPress}
      />
    </div>
  );
};

const Notifications = () => {
  const notifications = useAppSelector(notificationsSelector);

  if (notifications.length === 0) {
    return null;
  }

  return createPortal(
    <div className="notifications">
      {notifications.map((notification) => (
        <NotificationToast key={notification.id} {...notification} />
      ))}
    </div>,
    document.body,
  );
};

export default Notifications;
