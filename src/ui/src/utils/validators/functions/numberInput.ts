// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { NumberInputRange } from "@/utils/validators/types";
import { containsNullCharacters } from "@/utils/validators/utils";

export const isValidNumber = (value: string | undefined) =>
  !isNaN(Number(value));

export const isInRange =
  (range: NumberInputRange, nullable?: boolean) =>
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
