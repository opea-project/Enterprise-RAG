// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const SUPPORTED_FILE_EXTENSIONS = [
  // Document file extensions
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
  // Image file extensions
  "tiff",
  "jpg",
  "jpeg",
  "png",
  "svg",
  // Audio file extensions
  "mp3",
  "wav",
];

export const SUPPORTED_FILES_MIME_TYPES = [
  // Document MIME types
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
  // Image MIME types
  "image/tiff",
  "image/jpeg",
  "image/png",
  "image/svg+xml",
  // Audio MIME types
  "audio/mpeg", // .mp3
  "audio/wav", // .wav
];

export const LINK_ERROR_MESSAGE =
  "Enter valid URL that starts with protocol (http:// or https://).";
