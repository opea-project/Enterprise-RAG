// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const getUnsupportedFileExtensionMsg = ({
  value: file,
}: {
  value: File;
}) =>
  `The file ${file.name} has an unsupported extension\nPlease upload a file with one of supported formats listed below`;

export const getUnsupportedFileMIMETypeMsg = ({
  value: file,
}: {
  value: File;
}) =>
  `The file MIME type not recognized for ${file.name}\nPlease upload a file with a valid MIME type`;

export const getFilenameInvalidCharactersMsg = ({
  value: file,
}: {
  value: File;
}) =>
  `The file name - ${file.name} contains invalid characters\nPlease change the name of this file and try again`;

export const getFileSizeWithinLimitMsg =
  (clientMaxBodySize: number) =>
  ({ value: file }: { value: File }) =>
    `The file ${file.name} exceeds the size limit: ${clientMaxBodySize}MB\nPlease upload a smaller file`;
