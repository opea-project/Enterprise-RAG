// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface ServiceDetailsResponse {
  apiVersion: string;
  kind: string;
  metadata: Metadata;
  spec: Spec;
  status: Status;
}

interface Metadata {
  annotations: Record<string, string>;
  creationTimestamp: string;
  generation: number;
  labels: Record<string, string>;
  managedFields: ManagedField[];
  name: string;
  namespace: string;
  resourceVersion: string;
  uid: string;
}

interface ManagedField {
  apiVersion: string;
  fieldsType: string;
  fieldsV1: Record<string, never>;
  manager: string;
  operation: string;
  time: string;
  subresource?: string;
}

interface Spec {
  nodes: Nodes;
  routerConfig: RouterConfig;
}

interface Nodes {
  root: Root;
}

interface Root {
  routerType: string;
  steps: Step[];
}

interface Step {
  internalService: InternalService;
  name: string;
  data?: string;
}

interface InternalService {
  config?: Record<string, string>;
  serviceName: string;
  isDownstreamService?: boolean;
}

interface RouterConfig {
  name: string;
  serviceName: string;
}

interface Status {
  accessUrl: string;
  annotations: Record<string, string>;
  condition: Record<string, never>;
  status: string;
}
