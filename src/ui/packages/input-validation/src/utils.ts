// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { NULL_CHARS_REGEX } from "@/constants";

const containsNullCharacters = (input: string) => NULL_CHARS_REGEX.test(input);

const getFileExtension = (file: File) =>
  file.name.split(".").pop()?.toLowerCase();

export { containsNullCharacters, getFileExtension };
