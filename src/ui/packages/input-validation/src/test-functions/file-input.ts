// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FILE_EXTENSIONS_WITHOUT_MIME_TYPES } from "@/constants";
import { FileArrayTestFunction, FileTestFunction } from "@/types";
import { containsNullCharacters, getFileExtension } from "@/utils";

export const isFileExtensionSupported =
  (supportedFileExtensions: string[]): FileTestFunction =>
  (file) => {
    if (!(file instanceof File)) {
      return false;
    }

    const fileExtension = getFileExtension(file);
    const isFileExtensionValid =
      fileExtension !== undefined &&
      supportedFileExtensions.includes(fileExtension);

    return isFileExtensionValid;
  };

export const isMIMETypeSupported =
  (supportedFilesMIMETypes: string[]): FileTestFunction =>
  (file) => {
    if (!(file instanceof File)) {
      return false;
    }

    const fileExtension = getFileExtension(file);
    const isMIMETypeUnavailable =
      fileExtension !== undefined &&
      FILE_EXTENSIONS_WITHOUT_MIME_TYPES.includes(fileExtension);

    if (isMIMETypeUnavailable) {
      return true;
    } else {
      const fileMIMEType = file.type;
      return supportedFilesMIMETypes.includes(fileMIMEType);
    }
  };

export const noInvalidCharactersInFileName: FileTestFunction = (file) => {
  if (!(file instanceof File)) {
    return false;
  }

  const fileName = file.name;
  return fileName !== "" && !containsNullCharacters(fileName);
};

export const totalFileSizeWithinLimit =
  (clientMaxBodySize: number): FileArrayTestFunction =>
  (files) => {
    if (
      files === undefined ||
      !files.every((file) => file instanceof File) ||
      typeof clientMaxBodySize !== "number"
    ) {
      return false;
    }

    const totalSize = files.reduce((sum, file) => sum + file.size, 0);
    return totalSize <= clientMaxBodySize * 1024 * 1024;
  };

export const individualFileSizeWithinLimit =
  (clientMaxBodySize: number): FileTestFunction =>
  (file) => {
    if (!(file instanceof File)) {
      return false;
    }

    const fileSizeInMB = file.size / (1024 * 1024);
    return fileSizeInMB <= clientMaxBodySize;
  };
