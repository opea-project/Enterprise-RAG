// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import DOMPurify from "dompurify";
import { toASCII } from "punycode";
import { validate as isUuidValid } from "uuid";

const isSafeHref = (href: string | undefined) => {
  const sanitizedHref = sanitizeHref(href);
  return href === sanitizedHref;
};

const isPunycodeSafe = (input: string) => {
  const punycodeInput = toASCII(input);
  return input === punycodeInput;
};

const constructUrlWithUuid = (baseUrl: string, uuid: string) => {
  if (!isUuidValid(uuid)) {
    throw new Error(`Invalid UUID format: ${uuid}`);
  }

  const encodedUuid = encodeURIComponent(uuid);
  return baseUrl.replace("{uuid}", encodedUuid);
};

const tryDecode = (value: string) => {
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

const sanitizeString = (value: string) => {
  const decodedValue = tryDecode(value);
  return DOMPurify.sanitize(decodedValue);
};

const sanitizeHref = (href: string | undefined) => {
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

export {
  constructUrlWithUuid,
  isPunycodeSafe,
  isSafeHref,
  sanitizeHref,
  sanitizeString,
};
