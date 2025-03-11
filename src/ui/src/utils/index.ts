// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import DOMPurify from "dompurify";
import { toASCII } from "punycode";

const getPunycodeHref = (href: string | undefined) => {
  if (!href) {
    return href;
  }

  const decodedHref = decodeURIComponent(href);
  return toASCII(decodedHref);
};

const isHrefSafe = (href: string | undefined) => getPunycodeHref(href) === href;

const isPunycodeSafe = (input: string) => {
  const punycodeInput = toASCII(input);
  return input === punycodeInput;
};

const sanitizeString = (value: string) => {
  const decodedValue = decodeURIComponent(value);
  return DOMPurify.sanitize(decodedValue);
};

export { getPunycodeHref, isHrefSafe, isPunycodeSafe, sanitizeString };
