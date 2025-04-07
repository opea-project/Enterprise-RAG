// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentNumberInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { RetrieverArgs } from "@/features/admin-panel/control-plane/config/retriever";
import { getToken, refreshToken } from "@/lib/auth";

interface PostRetrieverQueryRequestBody extends RetrieverArgs {
  query: string;
  reranker: boolean;
  top_n: ServiceArgumentNumberInputValue;
  rerank_score_threshold: ServiceArgumentNumberInputValue;
}

export const postRetrieverQuery = async (
  query: string,
  retrieverArgs: RetrieverArgs,
  rerankerTopN: ServiceArgumentNumberInputValue,
  rerankerScoreThreshold: ServiceArgumentNumberInputValue,
  isRerankerEnabled: boolean,
) => {
  await refreshToken();

  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);
  headers.append("Content-Type", "application/json");

  const requestBody: PostRetrieverQueryRequestBody = {
    ...retrieverArgs,
    query,
    top_n: rerankerTopN,
    rerank_score_threshold: rerankerScoreThreshold,
    reranker: isRerankerEnabled,
  };

  const response = await fetch("/api/v1/edp/retrieve", {
    method: "POST",
    headers,
    body: JSON.stringify(requestBody),
  });

  if (response.ok) {
    return await response.text();
  } else {
    throw new Error(`Failed to get response from Retriever.
      Status: ${response.status}.
      Message: ${response.statusText}`);
  }
};
