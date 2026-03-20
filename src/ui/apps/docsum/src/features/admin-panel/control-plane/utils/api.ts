// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const SERVICE_NODE_IDS = [
  "docsum",
  "llm",
  "llm_model_server",
  "text_compression",
  "text_extractor",
  "text_splitter",
] as const;

export const SERVICE_NAME_NODE_ID_MAP: Record<
  string,
  (typeof SERVICE_NODE_IDS)[number]
> = {
  "v1:docsum-svc": "docsum",
  "v1:llm-svc": "llm",
  "v1:text-compression-svc": "text_compression",
  "v1:text-extractor-svc": "text_extractor",
  "v1:text-splitter-svc": "text_splitter",
  "v1:vllm-service-m": "llm_model_server",
};
