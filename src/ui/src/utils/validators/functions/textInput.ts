// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { isPunycodeSafe } from "@/utils";
import { containsNullCharacters } from "@/utils/validators/utils";

export const noEmpty =
  (emptyValueAllowed?: boolean) => (value: string | undefined) => {
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

export const containsRequiredValues =
  (requiredValues: string[]) => (value: string | undefined) => {
    if (value !== undefined && requiredValues.length > 0) {
      return !requiredValues.some(
        (requiredValue) => !value.includes(requiredValue),
      );
    } else {
      return false;
    }
  };
