// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// eslint-disable-next-line no-control-regex
export const NULL_CHARS_REGEX = /(\x00|\u0000|\0|%00)/;

export const FILE_EXTENSIONS_WITHOUT_MIME_TYPES: string[] = [
  "md",
  "jsonl",
  "yaml",
  "adoc",
];
