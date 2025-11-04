// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceStatus } from "@intel-enterprise-rag-ui/control-plane";

import { NamespaceStatus } from "@/features/admin-panel/control-plane/types/api/namespaceStatus";

export type GetServicesDataResponse = FetchedServicesData;

export interface FetchedServicesData {
  details: FetchedServiceDetails;
}

export interface FetchedServiceDetails {
  [serviceNodeId: string]: {
    status?: ServiceStatus;
    details?: { [key: string]: string };
  };
}

export type GetServicesDetailsResponse = NamespaceStatus;
