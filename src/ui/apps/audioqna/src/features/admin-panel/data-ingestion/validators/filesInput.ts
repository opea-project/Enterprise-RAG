// Copyright (C) 2024-2026 Intel Corporation
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
import { z } from "zod";

import { CLIENT_MAX_BODY_SIZE } from "@/config/api";
import {
  SUPPORTED_FILE_EXTENSIONS,
  SUPPORTED_FILES_MIME_TYPES,
} from "@/features/admin-panel/data-ingestion/utils/constants";

const validationSchema = z
  .array(
    z
      .instanceof(File)
      .refine(isFileExtensionSupported(SUPPORTED_FILE_EXTENSIONS), (file) => ({
        message: getUnsupportedFileExtensionMsg({ value: file }),
      }))
      .refine(isMIMETypeSupported(SUPPORTED_FILES_MIME_TYPES), (file) => ({
        message: getUnsupportedFileMIMETypeMsg({ value: file }),
      }))
      .refine(noInvalidCharactersInFileName, (file) => ({
        message: getFilenameInvalidCharactersMsg({ value: file }),
      })),
  )
  .refine(totalFileSizeWithinLimit(CLIENT_MAX_BODY_SIZE), {
    message: getFileSizeWithinLimitMsg(CLIENT_MAX_BODY_SIZE)({
      value: new File([], ""),
    }),
  });

export const validateFileInput = async (files: File[] | FileList) => {
  await validationSchema.parseAsync(Array.from(files));
};
