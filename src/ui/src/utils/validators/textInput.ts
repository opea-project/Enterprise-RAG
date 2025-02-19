// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { containsNullCharacters, isPunycodeSafe } from "@/utils/validators";

export const isValidNumber = (value: string | undefined) =>
  !isNaN(Number(value));

export const isInRange =
  (nullable: boolean, range: { min: number; max: number }) =>
  (value: string | undefined) => {
    if (value === undefined) {
      return false;
    } else {
      if (value === "") {
        return nullable;
      } else {
        if (containsNullCharacters(value)) {
          return false;
        }

        if (!nullable && value && value.trim() === "") {
          return false;
        } else {
          if (isValidNumber(value)) {
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
        if (containsNullCharacters(value)) {
          return false;
        }

        const isValueEmpty = value.trim() === "";
        return emptyValueAllowed ? true : !isValueEmpty;
      }
    }
  };

export const noInvalidCharacters =
  (): ((value: string) => boolean) => (value: string) =>
    !containsNullCharacters(value) && isPunycodeSafe(value);
