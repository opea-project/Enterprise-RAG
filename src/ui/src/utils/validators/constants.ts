// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const CLIENT_MAX_BODY_SIZE = 64; // 64 MB - src/ui/default.conf - client_max_body_size 64m

// eslint-disable-next-line no-control-regex
export const NULL_CHARS_REGEX = /(\x00|\u0000|\0|%00)/;

export const FILE_EXTENSIONS_WITHOUT_MIME_TYPES: string[] = [
  "md",
  "jsonl",
  "yaml",
];
