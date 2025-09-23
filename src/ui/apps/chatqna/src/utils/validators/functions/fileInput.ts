// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AnyObject, TestFunction } from "yup";

import {
  clientMaxBodySize,
  fileExtensionsWithoutMIMETypes,
} from "@/utils/validators/constants";
import { containsNullCharacters } from "@/utils/validators/utils";

type FileTestFunction = TestFunction<File | undefined, AnyObject>;
type FileArrayTestFunction = TestFunction<
  (File | undefined)[] | undefined,
  AnyObject
>;

const getFileExtension = (file: File) =>
  file.name.split(".").pop()?.toLowerCase();

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
      fileExtensionsWithoutMIMETypes.includes(fileExtension);

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

export const totalFileSizeWithinLimit: FileArrayTestFunction = (files) => {
  if (files === undefined || !files.every((file) => file instanceof File)) {
    return false;
  }

  const totalSize = files.reduce((sum, file) => sum + file.size, 0);
  return totalSize <= clientMaxBodySize * 1024 * 1024;
};
