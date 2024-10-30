// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { TestFunction } from "yup";

const nullCharacters = ["%00", "\0", "\\0", "\\x00", "\\u0000"];

export const isInRange =
  (nullable: boolean, range: { min: number; max: number }) =>
  (value: string | undefined) => {
    if (value === undefined) {
      return false;
    } else {
      if (value === "") {
        return nullable;
      } else {
        if (nullCharacters.some((char) => value.includes(char))) {
          return false;
        }

        if (!nullable && value && value.trim() === "") {
          return false;
        } else {
          const isValidNumber = !isNaN(parseFloat(value));
          if (isValidNumber) {
            const { min, max } = range;
            const numericValue = parseFloat(value);
            return numericValue >= min && numericValue <= max;
          } else {
            return false;
          }
        }
      }
    }
  };

export const noEmpty =
  (emptyValueAllowed: boolean) => (value: string | undefined) => {
    if (value === undefined) {
      return false;
    } else {
      if (value === "") {
        return emptyValueAllowed;
      } else {
        if (nullCharacters.some((char) => value.includes(char))) {
          return false;
        }

        const isValueEmpty = value.trim() === "";
        return emptyValueAllowed ? true : !isValueEmpty;
      }
    }
  };

export const unsupportedFileExtension =
  (acceptedFileTypesArray: string[]): TestFunction =>
  (value) => {
    const file = value as File;
    return acceptedFileTypesArray.some((type) => file.name.endsWith(type));
  };

export const improperCharacters =
  (): ((value: string) => boolean) => (value: string) =>
    !nullCharacters.some((char) => value.includes(char));

export const fileNameImproperCharacters = (): TestFunction => (value) => {
  const file = value as File;
  const fileName = file.name;
  return !nullCharacters.some((char) => fileName.includes(char));
};
