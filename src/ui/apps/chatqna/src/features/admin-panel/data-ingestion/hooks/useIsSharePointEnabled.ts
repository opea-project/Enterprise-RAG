// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useGetSharePointSitesQuery } from "@/features/admin-panel/data-ingestion/api/edpApi";

/**
 * Returns whether SharePoint integration is enabled (i.e. the backend did NOT
 * respond with a 404 / "not configured" error on the sites endpoint).
 */
const useIsSharePointEnabled = () => {
  const { error } = useGetSharePointSitesQuery();

  if (!error || !("status" in error)) return true;
  if (error.status !== 404) return true;

  const data = error.data as { detail?: string } | undefined;
  return !(
    typeof data?.detail === "string" && data.detail.includes("not configured")
  );
};

export default useIsSharePointEnabled;
