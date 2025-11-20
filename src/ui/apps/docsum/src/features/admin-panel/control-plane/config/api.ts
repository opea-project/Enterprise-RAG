// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const API_ENDPOINTS = {
  GET_SERVICES_DETAILS: "/api/v1/docsum/status",
} as const;

export const ERROR_MESSAGES = {
  GET_SERVICES_DETAILS: "Failed to fetch services details",
  GET_SERVICES_DATA: "Failed to fetch services data",
} as const;
