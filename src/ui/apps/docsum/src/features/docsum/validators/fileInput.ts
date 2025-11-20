// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  getFilenameInvalidCharactersMsg,
  getFileSizeWithinLimitMsg,
  getUnsupportedFileExtensionMsg,
  getUnsupportedFileMIMETypeMsg,
  individualFileSizeWithinLimit,
  isFileExtensionSupported,
  isMIMETypeSupported,
  noInvalidCharactersInFileName,
} from "@intel-enterprise-rag-ui/input-validation";
import { mixed, ValidationError } from "yup";

import { CLIENT_MAX_BODY_SIZE } from "@/config/api";
import {
  SUPPORTED_FILE_EXTENSIONS,
  SUPPORTED_FILES_MIME_TYPES,
} from "@/features/docsum/utils/fileInput";

const validationSchema = mixed<File>()
  .test(
    "supported-file-extension",
    getUnsupportedFileExtensionMsg,
    isFileExtensionSupported(SUPPORTED_FILE_EXTENSIONS),
  )
  .test(
    "supported-file-mime-type",
    getUnsupportedFileMIMETypeMsg,
    isMIMETypeSupported(SUPPORTED_FILES_MIME_TYPES),
  )
  .test(
    "no-invalid-characters-in-file-name",
    getFilenameInvalidCharactersMsg,
    noInvalidCharactersInFileName,
  )
  .test(
    "file-size-within-limit",
    getFileSizeWithinLimitMsg(CLIENT_MAX_BODY_SIZE),
    individualFileSizeWithinLimit(CLIENT_MAX_BODY_SIZE),
  );

export const validateFileInput = async (file: File) => {
  try {
    await validationSchema.validate(file);
    return "";
  } catch (error) {
    return (error as ValidationError).message;
  }
};
