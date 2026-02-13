// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { v4 as uuidv4 } from "uuid";

import { Notification, NotificationSeverity } from "@/Notifications/types";

interface NotificationsState {
  notifications: Notification[];
}

const initialState: NotificationsState = {
  notifications: [],
};

const notificationsSlice = createSlice({
  name: "notificationsSlice",
  initialState,
  reducers: {
    addNotification(
      state,
      action: PayloadAction<{
        severity: NotificationSeverity;
        text: string;
      }>,
    ) {
      const { severity, text } = action.payload;
      const newNotification = {
        id: uuidv4(),
        severity,
        text,
      };
      state.notifications = [...state.notifications, newNotification];
    },
    deleteNotification(state, action: PayloadAction<string>) {
      const notificationId = action.payload;
      state.notifications = state.notifications.filter(
        (notification) => notification.id !== notificationId,
      );
    },
  },
});

export const { addNotification, deleteNotification } =
  notificationsSlice.actions;
export const selectNotifications = (state: {
  notifications: NotificationsState;
}) => state.notifications.notifications;

export const notificationsReducer = notificationsSlice.reducer;
