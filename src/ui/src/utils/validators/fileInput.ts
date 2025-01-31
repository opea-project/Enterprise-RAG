// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AnyObject, TestFunction } from "yup";

import {
  supportedFileExtensions,
  supportedMIMETypes,
} from "@/utils/data-ingestion/files-input";
import { containsNullCharacters } from "@/utils/validators";
import {
  CLIENT_MAX_BODY_SIZE,
  FILE_EXTENSIONS_WITHOUT_MIME_TYPES,
} from "@/utils/validators/constants";

type FileTestFunction = TestFunction<File | undefined, AnyObject>;
type FileArrayTestFunction = TestFunction<
  (File | undefined)[] | undefined,
  AnyObject
>;

const getFileExtension = (file: File) =>
  file.name.split(".").pop()?.toLowerCase();

export const isFileExtensionSupported: FileTestFunction = (file) => {
  if (!(file instanceof File)) {
    return false;
  }

  const fileExtension = getFileExtension(file);
  const isFileExtensionValid =
    fileExtension !== undefined &&
    supportedFileExtensions.includes(fileExtension);

  return isFileExtensionValid;
};

export const isMIMETypeSupported: FileTestFunction = (file) => {
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
    return supportedMIMETypes.includes(fileMIMEType);
  }
};

export const noInvalidCharactersInFileName: FileTestFunction = (file) => {
  if (!(file instanceof File)) {
    return false;
  }

  const fileName = file.name;
  return fileName !== "" && !containsNullCharacters(fileName);
};

export const totalFileSizeWithinLimit: FileArrayTestFunction = (files) => {
  if (files === undefined || !files.every((file) => file instanceof File)) {
    return false;
  }

  const totalSize = files.reduce((sum, file) => sum + file.size, 0);
  return totalSize <= CLIENT_MAX_BODY_SIZE * 1024 * 1024;
};
