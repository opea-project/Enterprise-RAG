// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { TestFunction } from "yup";

import { containsNullCharacters } from "@/utils/validators";
import {
  CLIENT_MAX_BODY_SIZE,
  FILE_EXTENSIONS_WITHOUT_MIME_TYPES,
} from "@/utils/validators/constants";

const getFileExtension = (file: File) =>
  file.name.split(".").pop()?.toLowerCase();

export const isFileExtensionSupported =
  (acceptedExtensions: string[]): TestFunction =>
  (value) => {
    const file = value as File;
    const fileExtension = getFileExtension(file);
    const isFileExtensionValid =
      fileExtension !== undefined && acceptedExtensions.includes(fileExtension);

    return isFileExtensionValid;
  };

export const isMIMETypeSupported =
  (acceptedMIMETypes: string[]): TestFunction =>
  (value) => {
    const file = value as File;
    const fileExtension = getFileExtension(file);
    const isMIMETypeUnavailable =
      fileExtension !== undefined &&
      FILE_EXTENSIONS_WITHOUT_MIME_TYPES.includes(fileExtension);

    if (isMIMETypeUnavailable) {
      return true;
    } else {
      const fileMIMEType = file.type;
      return acceptedMIMETypes.includes(fileMIMEType);
    }
  };

export const noInvalidCharactersInFileName = (): TestFunction => (value) => {
  const file = value as File;
  const fileName = file.name;
  return !containsNullCharacters(fileName);
};

export const totalFileSizeWithinLimit = (): TestFunction => (value) => {
  const files = value as File[];
  const totalSize = files.reduce((sum, file) => sum + file.size, 0);
  return totalSize <= CLIENT_MAX_BODY_SIZE * 1024 * 1024;
};
