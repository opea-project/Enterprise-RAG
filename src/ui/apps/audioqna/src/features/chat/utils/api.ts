// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const validateAudioBlob = (blob: Blob) => {
  if (blob.size === 0) {
    throw new Error("No audio received");
  }

  if (blob.type && !blob.type.startsWith("audio/")) {
    throw new Error(`Invalid content type: expected audio/*, got ${blob.type}`);
  }
};

export const isAbortError = (err: unknown) =>
  (err instanceof Error && err.name === "AbortError") ||
  (err instanceof DOMException && err.name === "AbortError") ||
  (typeof err === "object" &&
    err !== null &&
    "name" in err &&
    err.name === "AbortError");
