// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { titleCaseString } from "@intel-enterprise-rag-ui/utils";

export const formatServiceDetailValue = (value: string) => {
  const serviceDetailsValuesMap: Record<string, string> = {
    // Connectors
    langchain: "LangChain",
    llama_index: "LlamaIndex",
    // Model Servers
    torchserve: "TorchServe",
    tei: "TEI",
    tgi: "TGI",
    ovms: "OpenVino™ Model Server",
    mosec: "Mosec",
    vllm: "vLLM",
    // Databases
    redis: "Redis",
  };

  if (serviceDetailsValuesMap[value]) {
    return serviceDetailsValuesMap[value];
  }

  return titleCaseString(value);
};
