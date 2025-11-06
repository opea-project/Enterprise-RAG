// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import DOMPurify from "dompurify";
import { toASCII } from "punycode";
import { validate as isUuidValid } from "uuid";

import {
  ACRONYMS,
  FILENAME_MAX_LENGTH,
  FILENAME_UNSAFE_CHARS_REGEX,
} from "@/constants";

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
 * Formats a file size in bytes into a human-readable string with appropriate units.
 *
 * @param fileSize - The file size in bytes.
 * @returns A formatted string representing the file size in B, KB, MB, GB, or TB.
 *
 * @example
 * ```typescript
 * formatFileSize(1024); // "1.0 KB"
 * formatFileSize(123456789); // "117.7 MB"
 * formatFileSize(0); // "0 B"
 * ```
 */
export const formatFileSize = (fileSize: number) => {
  const units = ["B", "KB", "MB", "GB", "TB"];

  if (fileSize === 0) {
    return "0 B";
  }
  const n = 1024;
  const i = Math.floor(Math.log(fileSize) / Math.log(n));
  let size: number | string = parseFloat(String(fileSize / Math.pow(n, i)));
  if (fileSize > n) {
    size = size.toFixed(1);
  }

  const unit = units[i];
  return `${size} ${unit}`;
};

/**
 * Converts a snake_case string to Title Case, preserving ACRONYMS (LLM, DB etc.).
 * @param {string} value - The snake_case string.
 * @returns {string} The Title Case string.
 */
export const formatSnakeCaseToTitleCase = (value: string) =>
  value
    .split("_")
    .map((str) => (ACRONYMS.includes(str) ? str : titleCaseString(str)))
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
 * Checks if a string is safe punycode.
 * @param {string} input - The input string.
 * @returns {boolean} True if input is safe punycode, false otherwise.
 */
export const isPunycodeSafe = (input: string) => {
  const punycodeInput = toASCII(input);
  return input === punycodeInput;
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
 * Creates a new `File` object with a sanitized file name.
 *
 * This function takes an existing `File` object, sanitizes its name using the `sanitizeFileName` function,
 * and returns a new `File` object with the sanitized name while preserving the original file's content and type.
 *
 * @param file - The original `File` object to be sanitized.
 * @returns A new `File` object with a sanitized file name.
 */
export const sanitizeFile = (file: File) => {
  const sanitizedFileName = sanitizeFileName(file.name);
  return new File([file], sanitizedFileName, { type: file.type });
};

/**
 * Sanitizes a file name by normalizing Unicode characters, replacing unsafe characters,
 * truncating to a maximum length, and encoding/decoding to expose homoglyphs and unusual characters.
 *
 * @param filename - The original file name to sanitize.
 * @returns The sanitized file name safe for use.
 */
export const sanitizeFileName = (filename: string) => {
  const normalizedFileName = filename.normalize("NFKC");
  const sanitizedFileName = normalizedFileName.replace(
    FILENAME_UNSAFE_CHARS_REGEX,
    "_",
  );
  const truncatedFileName = sanitizedFileName.substring(0, FILENAME_MAX_LENGTH);

  // Encode/decode cycle helps expose homoglyphs and unusual characters
  return decodeURIComponent(encodeURIComponent(truncatedFileName));
};

/**
 * Sanitizes the names of the provided files by applying the `sanitizeFileName` function
 * to each file's name and returns new `File` objects with the sanitized names.
 *
 * @param files - An array of `File` objects to be sanitized.
 * @returns A new array of `File` objects with sanitized file names.
 */
export const sanitizeFiles = (files: File[]): File[] => files.map(sanitizeFile);

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
