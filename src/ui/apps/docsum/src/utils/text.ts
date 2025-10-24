// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const shortenText = (text: string, maxLength: number = 20): string => {
  const trimmedText = text.trim();
  return trimmedText.length > maxLength
    ? `${trimmedText.slice(0, maxLength)}...`
    : trimmedText;
};
