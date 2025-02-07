// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { toASCII } from "punycode";

import { NULL_CHARS_REGEX } from "@/utils/validators/constants";

const containsNullCharacters = (input: string) => NULL_CHARS_REGEX.test(input);

const isPunycodeSafe = (input: string) => {
  const punycodeInput = toASCII(input);
  return input === punycodeInput;
};

export { containsNullCharacters, isPunycodeSafe };
