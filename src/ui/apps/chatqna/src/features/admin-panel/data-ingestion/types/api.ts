// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export type FileSyncAction = "add" | "no action" | "delete" | "update";

export interface FileSyncDataItem {
  action: FileSyncAction;
  bucket_name: string;
  object_name: string;
}

export interface PostFileToExtractTextRequest {
  uuid: string;
  queryParams?: PostToExtractTextQueryParams;
}

export interface PostToExtractTextQueryParams extends Record<
  string,
  number | boolean | undefined | string
> {
  chunk_size?: number;
  chunk_overlap?: number;
  use_semantic_chunking?: boolean;
}

export interface GetS3BucketsListResponseData {
  buckets: string[];
}

export interface PostFileRequest {
  url: string;
  file: File;
}

export interface SharePointSiteItem {
  id: string;
  name: string;
  display_name: string | null;
  web_url: string | null;
}

export interface SharePointSitesResponse {
  sites: SharePointSiteItem[];
}

export interface PostSharePointSiteRequest {
  site_url: string;
}

export interface SharePointSyncDataItem {
  action: FileSyncAction;
  site_name: string;
  object_name: string;
}

export interface SharePointUploadRequest {
  site_id: string;
  file: File;
}

export interface SharePointFileUrlRequest {
  site_name: string;
  object_name: string;
}

export interface SharePointFileUrlResponse {
  url: string;
}
