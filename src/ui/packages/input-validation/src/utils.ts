// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ZodError } from "zod";

import { NULL_CHARS_REGEX } from "@/constants";

const containsNullCharacters = (input: string) => NULL_CHARS_REGEX.test(input);

const getFileExtension = (file: File) =>
  file.name.split(".").pop()?.toLowerCase();

/**
 * Extracts a readable error message from a validation error.
 * Returns the first error message from a ZodError, or a default message for other errors.
 * @param error - The error object to extract the message from
 * @param defaultMessage - The default message to return if extraction fails (default: "Validation error")
 * @returns The extracted error message
 */
const getValidationErrorMessage = (
  error: unknown,
  defaultMessage: string = "Validation error",
): string => {
  if (error instanceof ZodError) {
    return error.errors[0]?.message || defaultMessage;
  }
  return defaultMessage;
};

export { containsNullCharacters, getFileExtension, getValidationErrorMessage };
