// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { array, mixed, ValidationError } from "yup";

import {
  supportedFileExtensions,
  supportedFilesMIMETypes,
} from "@/features/admin-panel/data-ingestion/utils/constants";
import { clientMaxBodySize } from "@/utils/validators/constants";
import {
  isFileExtensionSupported,
  isMIMETypeSupported,
  noInvalidCharactersInFileName,
  totalFileSizeWithinLimit,
} from "@/utils/validators/functions/fileInput";

const getUnsupportedFileExtensionMsg = ({ value: file }: { value: File }) =>
  `The file ${file.name} has an unsupported extension\nPlease upload a file with one of supported formats listed below`;
const getUnsupportedFileMIMETypeMsg = ({ value: file }: { value: File }) =>
  `The file MIME type not recognized for ${file.name}\nPlease upload a file with a valid MIME type`;
const getFilenameInvalidCharactersMsg = ({ value: file }: { value: File }) =>
  `The file name - ${file.name} contain invalid characters\nPlease change the name of this file and try again`;

const totalFileSizeWithinLimitMsg = `Total upload size will exceed the limit: ${clientMaxBodySize}MB\nPlease upload files separately or in smaller batches`;

const validationSchema = array()
  .of(
    mixed<File>()
      .test(
        "supported-file-extension",
        getUnsupportedFileExtensionMsg,
        isFileExtensionSupported(supportedFileExtensions),
      )
      .test(
        "supported-file-mime-type",
        getUnsupportedFileMIMETypeMsg,
        isMIMETypeSupported(supportedFilesMIMETypes),
      )
      .test(
        "no-invalid-characters-in-file-name",
        getFilenameInvalidCharactersMsg,
        noInvalidCharactersInFileName,
      ),
  )
  .test(
    "total-file-size-within-limit",
    totalFileSizeWithinLimitMsg,
    totalFileSizeWithinLimit,
  );

export const validateFileInput = async (files: File[] | FileList) => {
  try {
    await validationSchema.validate(Array.from(files));
    return "";
  } catch (error) {
    return (error as ValidationError).message;
  }
};
