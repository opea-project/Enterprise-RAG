// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Notifications.scss";

import { ErrorIcon, SuccessIcon } from "@intel-enterprise-rag-ui/icons";
import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { useDispatch, useSelector } from "react-redux";

import { IconButton } from "@/IconButton/IconButton";
import { notificationsConfig } from "@/Notifications/config";
import {
  deleteNotification,
  selectNotifications,
} from "@/Notifications/notifications.slice";
import { Notification } from "@/Notifications/types";

type NotificationToastProps = Notification;

const NotificationToast = ({ id, text, severity }: NotificationToastProps) => {
  const dispatch = useDispatch();
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
        color={severity}
        icon="close-notification"
        aria-label="Dismiss notification"
        className="notification-toast__dismiss-btn"
        onPress={handleDismissBtnPress}
      />
    </div>
  );
};

/**
 * Notifications component for rendering notification toasts.
 * Uses React Portal to display notifications at the top level of the DOM.
 * Renders a list of notifications with dismiss functionality and auto-hide after a delay.
 */
export const Notifications = () => {
  const notifications = useSelector(selectNotifications);

  if (notifications.length === 0) {
    return null;
  }

  return createPortal(
    <div className="notifications">
      {notifications.map((notification: Notification) => (
        <NotificationToast key={notification.id} {...notification} />
      ))}
    </div>,
    document.body,
  );
};
