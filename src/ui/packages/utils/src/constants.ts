// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const ACRONYMS = ["LLM", "DB"];

export const FILENAME_MAX_LENGTH = 255;

// - Characters reserved for file systems (<>:"/\\|?*)
// - ASCII control characters (\x00-\x1F)
// eslint-disable-next-line no-control-regex
export const FILENAME_UNSAFE_CHARS_REGEX = new RegExp(/[<>:"/\\|?*\x00-\x1F]/g);
