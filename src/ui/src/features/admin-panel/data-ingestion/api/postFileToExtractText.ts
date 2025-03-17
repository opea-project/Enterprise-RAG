// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ExtractTextQueryParamsFormData } from "@/features/admin-panel/data-ingestion/types";
import { getToken, refreshToken } from "@/lib/auth";
import { constructUrlWithUuid } from "@/utils";

const createQueryParamsString = (
  queryParamsObj: ExtractTextQueryParamsFormData,
) => {
  const queryParamsEntries = Object.entries(queryParamsObj)
    .map(([key, value]) =>
      key === "table_strategy"
        ? [key, value === true ? "fast" : undefined]
        : [key, value],
    )
    .filter(([, value]) => value !== undefined);

  const queryParamsString = new URLSearchParams(
    Object.fromEntries(queryParamsEntries),
  ).toString();
  return queryParamsString;
};

export const postFileToExtractText = async (
  uuid: string,
  queryParamsObj?: ExtractTextQueryParamsFormData,
) => {
  await refreshToken();

  let url = constructUrlWithUuid("/api/v1/edp/file/{uuid}/extract", uuid);
  if (queryParamsObj) {
    const queryParamsString = createQueryParamsString(queryParamsObj);
    url += `?${queryParamsString}`;
  }

  const headers = new Headers();
  headers.append("Authorization", `Bearer ${getToken()}`);

  const response = await fetch(url, {
    method: "POST",
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to extract text from the file");
  }

  return await response.json();
};
