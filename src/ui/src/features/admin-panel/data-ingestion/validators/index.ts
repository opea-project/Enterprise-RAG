// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

const supportedFileLinksExtensions = ["html"];

export const notLinkToFile =
  (): ((value: string) => boolean) => (value: string) => {
    if (!value) return true;

    try {
      const url = new URL(value);
      const pathParts = url.pathname.split("/");
      const lastPart = pathParts.at(-1);

      // URLs ended with slash are not files
      if (lastPart === "") {
        return true;
      }

      // Check if the last part of URL pathname potentially contains a file extension
      if (lastPart && lastPart.includes(".")) {
        const extension = lastPart.split(".").at(-1)?.toLowerCase();
        if (extension === "") {
          return false;
        }

        // Check if the extension is not "html" that is the only supported extension
        return !extension || supportedFileLinksExtensions.includes(extension);
      }

      return true;
    } catch {
      return false;
    }
  };
