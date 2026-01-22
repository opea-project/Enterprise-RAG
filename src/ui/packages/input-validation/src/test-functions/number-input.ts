// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { NumberInputRange } from "@/types";
import { containsNullCharacters } from "@/utils";

export const isValidNumber = (value: string | undefined) =>
  !isNaN(Number(value));

export const isInRange =
  (range: NumberInputRange, isNullable?: boolean) =>
  (value: string | undefined) => {
    if (value === undefined) {
      return false;
    } else {
      if (value === "") {
        return isNullable;
      } else {
        if (containsNullCharacters(value)) {
          return false;
        }

        if (!isNullable && value && value.trim() === "") {
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
