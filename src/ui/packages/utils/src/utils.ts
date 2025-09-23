// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import DOMPurify from "dompurify";
import { toASCII } from "punycode";
import { validate as isUuidValid } from "uuid";

import { acronyms } from "@/constants";

declare global {
  interface Window {
    env?: Record<string, string>;
  }

  interface ImportMeta {
    env: {
      [key: `VITE_${string}`]: string;
      PROD: boolean;
    };
  }
}

/**
 * Constructs a URL by replacing {uuid} with the encoded UUID.
 * @param {string} baseUrl - The base URL containing {uuid}.
 * @param {string} uuid - The UUID to insert.
 * @returns {string} The constructed URL.
 * @throws {Error} If the UUID is invalid.
 */
export const constructUrlWithUuid = (baseUrl: string, uuid: string) => {
  if (!isUuidValid(uuid)) {
    throw new Error(`Invalid UUID format: ${uuid}`);
  }

  const encodedUuid = encodeURIComponent(uuid);
  return baseUrl.replace("{uuid}", encodedUuid);
};

/**
 * Downloads a Blob object as a file.
 * @param {Blob} blob - The blob to download.
 * @param {string} fileName - The name of the file to save.
 * @returns {void}
 */
export const downloadBlob = (blob: Blob, fileName: string) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  a.click();
  a.remove();
  setTimeout(() => window.URL.revokeObjectURL(url), 1000);
};

/**
 * Converts a snake_case string to Title Case, preserving acronyms (LLM, DB etc.).
 * @param {string} value - The snake_case string.
 * @returns {string} The Title Case string.
 */
export const formatSnakeCaseToTitleCase = (value: string) =>
  value
    .split("_")
    .map((str) => (acronyms.includes(str) ? str : titleCaseString(str)))
    .join(" ");

/**
 * Gets environment variable value from importMetaEnv or window.env.
 * Only supports development environments defined for Vite (VITE_* variables).
 * @template T
 * @param {Record<string, unknown>|undefined} importMetaEnv - The import.meta.env object.
 * @param {{ env?: Record<string, string> }|undefined} windowObj - The window object.
 * @param {T} envKey - The environment variable key.
 * @returns {string} The environment variable value.
 */
export const getAppEnv = <T extends string>(
  importMetaEnv: Record<string, unknown> | undefined,
  windowObj: { env?: Record<string, string> } | undefined,
  envKey: T,
): string => {
  const env = importMetaEnv;
  const isProd = env?.PROD ?? false;

  if (isProd) {
    return windowObj?.env?.[envKey] ?? "";
  } else {
    return (env?.[`VITE_${envKey}`] ?? "") as string;
  }
};

/**
 * Checks if a href is safe after sanitization.
 * @param {string|undefined} href - The href to check.
 * @returns {boolean} True if href is safe, false otherwise.
 */
export const isSafeHref = (href: string | undefined) => {
  const sanitizedHref = sanitizeHref(href);
  return href === sanitizedHref;
};

/**
 * Checks if a string is safe punycode.
 * @param {string} input - The input string.
 * @returns {boolean} True if input is safe punycode, false otherwise.
 */
export const isPunycodeSafe = (input: string) => {
  const punycodeInput = toASCII(input);
  return input === punycodeInput;
};

/**
 * Attempts to decode a URI component string.
 * @param {string} value - The value to decode.
 * @returns {string} The decoded value, or original if decoding fails.
 */
export const tryDecode = (value: string) => {
  let decodedValue = value;
  try {
    decodedValue = decodeURIComponent(value);
  } catch (error) {
    if (!(error instanceof URIError)) {
      throw error;
    }
  }
  return decodedValue;
};

/**
 * Sanitizes a href string using DOMPurify and punycode.
 * @param {string|undefined} href - The href to sanitize.
 * @returns {string|undefined} The sanitized href, or undefined if invalid.
 */
export const sanitizeHref = (href: string | undefined) => {
  if (!href) {
    return undefined;
  }

  try {
    const decodedHref = tryDecode(href);
    const asciiHref = toASCII(decodedHref);
    const sanitizedHref = DOMPurify.sanitize(asciiHref, {
      ALLOWED_TAGS: [],
      ALLOWED_ATTR: [],
    });
    return sanitizedHref;
  } catch {
    return undefined;
  }
};

/**
 * Sanitizes a string using DOMPurify.
 * @param {string|undefined} value - The string to sanitize.
 * @returns {string} The sanitized string.
 */
export const sanitizeString = (value: string | undefined) => {
  if (typeof value === "undefined") {
    return "";
  }
  const decodedValue = tryDecode(value);
  return DOMPurify.sanitize(decodedValue);
};

/**
 * Converts a string to Title Case.
 * @param {string} value - The string to convert.
 * @returns {string} The Title Case string.
 */
export const titleCaseString = (value: string) =>
  `${value.charAt(0).toUpperCase()}${value.slice(1).toLowerCase()}`;
