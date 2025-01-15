// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import * as Yup from "yup";
import { ValidationError } from "yup";

import { CLIENT_MAX_BODY_SIZE } from "@/utils/validators/constants";
import {
  isFileExtensionSupported,
  isMIMETypeSupported,
  noInvalidCharactersInFileName,
  totalFileSizeWithinLimit,
} from "@/utils/validators/fileInput";

const DOCUMENTS_SUPPORTED_FILE_EXTENSIONS = [
  "pdf",
  "html",
  "txt",
  "doc",
  "docx",
  "ppt",
  "pptx",
  "md",
  "xml",
  "json",
  "jsonl",
  "yaml",
  "xls",
  "xlsx",
  "csv",
];

const DOCUMENTS_SUPPORTED_MIME_TYPES = [
  "application/pdf",
  "text/html",
  "text/plain",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document", // .docx
  "application/vnd.ms-powerpoint",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation", // .pptx
  "application/xml",
  "text/xml",
  "application/json",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
  "text/csv",
];

const INPUT_FILE_ACCEPT = DOCUMENTS_SUPPORTED_FILE_EXTENSIONS.map(
  (extension) => `.${extension}`,
).join(",");

const SUPPORTED_FILE_FORMATS_MSG = `Supported file formats:  ${DOCUMENTS_SUPPORTED_FILE_EXTENSIONS.map(
  (extension) => extension.toUpperCase(),
).join(", ")}`;

const TOTAL_SIZE_LIMIT_MSG = `Single upload size limit: ${CLIENT_MAX_BODY_SIZE}MB`;

// - Characters reserved for file systems (<>:"/\\|?*)
// - ASCII control characters (\x00-\x1F)
// eslint-disable-next-line no-control-regex
const FILE_NAME_UNSAFE_CHARS_REGEX = new RegExp(/[<>:"/\\|?*\x00-\x1F]/g);
const FILE_NAME_MAX_LENGTH = 255;

const UNSUPPORTED_FILE_EXTENSION_MSG = (filename: string) =>
  `The file ${filename} has an unsupported file extension. Please upload a file with supported file format.`;
const UNSUPPORTED_FILE_MIME_TYPE_MSG = (filename: string) =>
  `The file type not recognized for ${filename}. Please upload a file with a valid format.`;
const FILE_NAME_INVALID_CHARACTERS_MSG = (filename: string) =>
  `The file name - ${filename} contain invalid characters. Please change the name of this file and try again.`;
const TOTAL_FILE_SIZE_WITHIN_LIMIT_MSG = `Total files size exceeds the limit: ${CLIENT_MAX_BODY_SIZE}MB. Please upload files separately or in smaller batches.`;

const validationSchema = Yup.array()
  .of(
    Yup.mixed()
      .test(
        "supported-file-extension",
        ({ value }) => UNSUPPORTED_FILE_EXTENSION_MSG((value as File).name),
        isFileExtensionSupported(DOCUMENTS_SUPPORTED_FILE_EXTENSIONS),
      )
      .test(
        "supported-file-mime-type",
        ({ value }) => UNSUPPORTED_FILE_MIME_TYPE_MSG((value as File).name),
        isMIMETypeSupported(DOCUMENTS_SUPPORTED_MIME_TYPES),
      )
      .test(
        "no-invalid-characters-in-file-name",
        ({ value }) => FILE_NAME_INVALID_CHARACTERS_MSG((value as File).name),
        noInvalidCharactersInFileName(),
      ),
  )
  .test(
    "total-file-size-within-limit",
    TOTAL_FILE_SIZE_WITHIN_LIMIT_MSG,
    totalFileSizeWithinLimit(),
  );

const validateDocuments = async (documents: File[] | FileList) => {
  try {
    await validationSchema.validate(Array.from(documents));
    return "";
  } catch (error) {
    return (error as ValidationError).message;
  }
};

const sanitizeFileName = (filename: string) => {
  const normalizedFileName = filename.normalize("NFKC");
  const sanitizedFileName = normalizedFileName.replace(
    FILE_NAME_UNSAFE_CHARS_REGEX,
    "_",
  );
  const truncatedFileName = sanitizedFileName.substring(
    0,
    FILE_NAME_MAX_LENGTH,
  );
  const encodedFileName = encodeURIComponent(truncatedFileName);
  return encodedFileName;
};

const sanitizeFiles = (files: File[]): File[] =>
  files.map((file) => {
    const sanitizedFileName = sanitizeFileName(file.name);
    return new File([file], sanitizedFileName, { type: file.type });
  });

export {
  INPUT_FILE_ACCEPT,
  sanitizeFiles,
  SUPPORTED_FILE_FORMATS_MSG,
  TOTAL_SIZE_LIMIT_MSG,
  validateDocuments,
};
