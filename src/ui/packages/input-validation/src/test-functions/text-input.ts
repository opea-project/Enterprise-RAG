// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { isPunycodeSafe } from "@intel-enterprise-rag-ui/utils";

import { containsNullCharacters } from "@/utils";

export const noEmpty =
  (isEmptyValueAllowed?: boolean) => (value: string | undefined) => {
    if (value === undefined) {
      return false;
    } else {
      if (value === "") {
        return isEmptyValueAllowed;
      } else {
        if (containsNullCharacters(value)) {
          return false;
        }

        const isValueEmpty = value.trim() === "";
        return isEmptyValueAllowed ? true : !isValueEmpty;
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

export const containsSupportedCommaSeparatedValues =
  (isCommaSeparated?: boolean, supportedValues?: string[]) =>
  (value: string | undefined) => {
    if (isCommaSeparated && supportedValues && supportedValues.length) {
      const values = value?.split(",");
      if (values && values.length) {
        return values.every((val) => supportedValues?.includes(val));
      } else {
        return true;
      }
    } else {
      return true;
    }
  };
