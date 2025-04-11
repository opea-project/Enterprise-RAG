// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const API_ENDPOINTS = {
  GET_SERVICES_PARAMETERS: "/v1/system_fingerprint/append_arguments",
  GET_SERVICES_DETAILS: "/api/v1/chatqa/status",
  CHANGE_ARGUMENTS: "/v1/system_fingerprint/change_arguments",
  POST_RETRIEVER_QUERY: "/api/v1/edp/retrieve",
} as const;

export const ERROR_MESSAGES = {
  GET_SERVICES_PARAMETERS: "Failed to fetch services parameters",
  GET_SERVICES_DETAILS: "Failed to fetch services details",
  GET_SERVICES_DATA: "Failed to fetch services data",
  CHANGE_ARGUMENTS: "Failed to change service arguments",
  POST_RETRIEVER_QUERY: "Failed to fetch retrieved documents",
} as const;
