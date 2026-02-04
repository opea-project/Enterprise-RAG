// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const API_ENDPOINTS = {
  GET_STATUS_AUDIO: "/api/v1/audio/status",
  GET_STATUS_CHATQA: "/api/v1/chatqa/status",
} as const;

export const ERROR_MESSAGES = {
  GET_STATUS: "Failed to fetch services status details",
} as const;
