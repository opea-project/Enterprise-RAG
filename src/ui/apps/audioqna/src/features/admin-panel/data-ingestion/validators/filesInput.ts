// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  getFilenameInvalidCharactersMsg,
  getFileSizeWithinLimitMsg,
  getUnsupportedFileExtensionMsg,
  getUnsupportedFileMIMETypeMsg,
  isFileExtensionSupported,
  isMIMETypeSupported,
  noInvalidCharactersInFileName,
  totalFileSizeWithinLimit,
} from "@intel-enterprise-rag-ui/input-validation";
import { array, mixed, ValidationError } from "yup";

import { CLIENT_MAX_BODY_SIZE } from "@/config/api";
import {
  SUPPORTED_FILE_EXTENSIONS,
  SUPPORTED_FILES_MIME_TYPES,
} from "@/features/admin-panel/data-ingestion/utils/constants";

const validationSchema = array()
  .of(
    mixed<File>()
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
      ),
  )
  .test(
    "total-file-size-within-limit",
    getFileSizeWithinLimitMsg(CLIENT_MAX_BODY_SIZE),
    totalFileSizeWithinLimit(CLIENT_MAX_BODY_SIZE),
  );

export const validateFileInput = async (files: File[] | FileList) => {
  try {
    await validationSchema.validate(Array.from(files));
    return "";
  } catch (error) {
    return (error as ValidationError).message;
  }
};
