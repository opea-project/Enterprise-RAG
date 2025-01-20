// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { array, mixed, ValidationError } from "yup";

import { CLIENT_MAX_BODY_SIZE } from "@/utils/validators/constants";
import {
  isFileExtensionSupported,
  isMIMETypeSupported,
  noInvalidCharactersInFileName,
  totalFileSizeWithinLimit,
} from "@/utils/validators/fileInput";

const supportedFileExtensions = [
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
  "tiff",
  "jpg",
  "jpeg",
  "png",
  "svg",
];

const supportedMIMETypes = [
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
  "image/tiff",
  "image/jpeg",
  "image/png",
  "image/svg+xml",
];

const fileInputAccept = supportedFileExtensions
  .map((extension) => `.${extension}`)
  .join(",");

const supportedFileFormatsMsg = `Supported file formats:  ${supportedFileExtensions
  .map((extension) => extension.toUpperCase())
  .join(", ")}`;

const totalSizeLimitMsg = `Single upload size limit: ${CLIENT_MAX_BODY_SIZE}MB`;

// - Characters reserved for file systems (<>:"/\\|?*)
// - ASCII control characters (\x00-\x1F)
// eslint-disable-next-line no-control-regex
const filenameUnsafeCharsRegex = new RegExp(/[<>:"/\\|?*\x00-\x1F]/g);
const filenameMaxLength = 255;

const getUnsupportedFileExtensionMsg = ({ value: file }: { value: File }) =>
  `The file ${file.name} has an unsupported extension\nPlease upload a file with one of supported formats listed below`;
const getUnsupportedFileMIMETypeMsg = ({ value: file }: { value: File }) =>
  `The file MIME type not recognized for ${file.name}\nPlease upload a file with a valid MIME type`;
const getFilenameInvalidCharactersMsg = ({ value: file }: { value: File }) =>
  `The file name - ${file.name} contain invalid characters\nPlease change the name of this file and try again`;

const totalFileSizeWithinLimitMsg = `Total upload size will exceed the limit: ${CLIENT_MAX_BODY_SIZE}MB\nPlease upload files separately or in smaller batches`;

const validationSchema = array()
  .of(
    mixed<File>()
      .test(
        "supported-file-extension",
        getUnsupportedFileExtensionMsg,
        isFileExtensionSupported,
      )
      .test(
        "supported-file-mime-type",
        getUnsupportedFileMIMETypeMsg,
        isMIMETypeSupported,
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

const validateFiles = async (files: File[] | FileList) => {
  try {
    await validationSchema.validate(Array.from(files));
    return "";
  } catch (error) {
    return (error as ValidationError).message;
  }
};

const sanitizeFileName = (filename: string) => {
  const normalizedFileName = filename.normalize("NFKC");
  const sanitizedFileName = normalizedFileName.replace(
    filenameUnsafeCharsRegex,
    "_",
  );
  const truncatedFileName = sanitizedFileName.substring(0, filenameMaxLength);
  const encodedFileName = encodeURIComponent(truncatedFileName);
  return encodedFileName;
};

const sanitizeFiles = (files: File[]): File[] =>
  files.map((file) => {
    const sanitizedFileName = sanitizeFileName(file.name);
    return new File([file], sanitizedFileName, { type: file.type });
  });

export {
  fileInputAccept,
  sanitizeFiles,
  supportedFileExtensions,
  supportedFileFormatsMsg,
  supportedMIMETypes,
  totalSizeLimitMsg,
  validateFiles,
};
