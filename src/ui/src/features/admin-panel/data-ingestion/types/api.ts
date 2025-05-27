// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface GetFilePresignedUrlRequest {
  fileName: string;
  method: GetFilePresignedUrlMethod;
  bucketName: string;
}

type GetFilePresignedUrlMethod = "GET" | "PUT" | "DELETE";

export interface PostFileToExtractTextRequest {
  uuid: string;
  queryParams?: PostFileToExtractTextQueryParams;
}

export interface PostFileToExtractTextQueryParams
  extends Record<string, number | boolean | undefined | string> {
  chunk_size?: number;
  chunk_overlap?: number;
  process_table?: boolean;
  table_strategy?: string;
}

export interface PostLinkToExtractTextQueryParams
  extends PostFileToExtractTextQueryParams {
}

export interface GetS3BucketsListResponseData {
  buckets: string[];
}

export interface PostFileRequest {
  url: string;
  file: File;
}

export interface DownloadFileRequest {
  presignedUrl: string;
  fileName: string;
}
