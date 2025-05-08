// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// - Characters reserved for file systems (<>:"/\\|?*)
// - ASCII control characters (\x00-\x1F)
// eslint-disable-next-line no-control-regex
export const filenameUnsafeCharsRegex = new RegExp(/[<>:"/\\|?*\x00-\x1F]/g);

export const filenameMaxLength = 255;

export const supportedFileExtensions = [
  "adoc",
  "pdf",
  "html",
  "txt",
  "doc",
  "docx",
  "ppt",
  "pptx",
  "md",
  "xml",
  "json",
  "jsonl",
  "yaml",
  "xls",
  "xlsx",
  "csv",
  "tiff",
  "jpg",
  "jpeg",
  "png",
  "svg",
];

export const supportedFilesMIMETypes = [
  "application/pdf",
  "text/html",
  "text/plain",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document", // .docx
  "application/vnd.ms-powerpoint",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation", // .pptx
  "application/xml",
  "text/xml",
  "application/json",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
  "text/csv",
  "image/tiff",
  "image/jpeg",
  "image/png",
  "image/svg+xml",
];

export const linkErrorMessage =
  "Enter valid URL that starts with protocol (http:// or https://).";
