// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { TextInput } from "@intel-enterprise-rag-ui/components";
import {
  getValidationErrorMessage,
  NumberInputRange,
} from "@intel-enterprise-rag-ui/input-validation";
import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEvent, FocusEvent, useEffect, useRef, useState } from "react";

import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/features/admin-panel/control-plane/types";
import { validateServiceArgumentNumberInput } from "@/features/admin-panel/control-plane/validators/service-arguments/numberInput";

export type ServiceArgumentNumberInputValue =
  | string
  | number
  | undefined
  | null;

interface ServiceArgumentNumberInputProps {
  name: string;
  value?: ServiceArgumentNumberInputValue;
  range: NumberInputRange;
  tooltipText?: string;
  isNullable?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
  onArgumentValidityChange: OnArgumentValidityChangeHandler;
}

const ServiceArgumentNumberInput = ({
  name,
  value,
  range,
  tooltipText,
  isNullable = false,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentNumberInputProps) => {
  // Ensure 0 renders and preserve user format while editing
  const [displayValue, setDisplayValue] = useState<string>(
    value !== null && value !== undefined ? String(value) : "",
  );
  const [isFocused, setIsFocused] = useState(false);
  const [isInvalid, setIsInvalid] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  // New: keep empty after blur and track last prop to detect external changes
  const [keepEmptyOnBlur, setKeepEmptyOnBlur] = useState(false);
  const lastPropValueRef = useRef<ServiceArgumentNumberInputValue>(value);

  useEffect(() => {
    // Only sync from prop when not editing; avoid dropping ".0"
    if (!isFocused) {
      const propChanged = value !== lastPropValueRef.current;

      // If user cleared and prop hasn't changed externally, keep the empty display
      if (keepEmptyOnBlur && !propChanged && displayValue === "") {
        return;
      }

      const next = value !== null && value !== undefined ? String(value) : "";
      if (displayValue !== next) {
        setDisplayValue(next);
      }

      lastPropValueRef.current = value;

      // If prop changed externally, allow future syncs again
      if (propChanged) {
        setKeepEmptyOnBlur(false);
      }
    }
  }, [value, isFocused, keepEmptyOnBlur, displayValue]);

  const validateInput = async (value: string) => {
    try {
      await validateServiceArgumentNumberInput(value, range, isNullable);
      setIsInvalid(false);
      setErrorMessage("");
      return true;
    } catch (validationError) {
      setIsInvalid(true);
      setErrorMessage(getValidationErrorMessage(validationError));
      return false;
    }
  };

  const handleChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setDisplayValue(newValue);
    const sanitizedValue = sanitizeString(newValue);
    setKeepEmptyOnBlur(sanitizedValue === "");

    const isValid = await validateInput(sanitizedValue);
    onArgumentValidityChange(name, !isValid);

    if (isValid) {
      // Preserve 0; only send null/undefined for empty
      let argumentValue: ServiceArgumentNumberInputValue;
      if (sanitizedValue === "") {
        argumentValue = isNullable ? null : undefined;
      } else {
        const parsed = parseFloat(sanitizedValue);
        argumentValue = Number.isNaN(parsed) ? null : parsed;
      }
      onArgumentValueChange(name, argumentValue);
    }
  };

  const handleFocus = () => setIsFocused(true);

  const handleBlur = async (event: FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);

    const sanitizedValue = sanitizeString(event.target.value);
    setKeepEmptyOnBlur(sanitizedValue === "");

    // Re-validate on blur
    const isValid = await validateInput(sanitizedValue);
    onArgumentValidityChange(name, !isValid);

    // If cleared, explicitly commit empty so the model matches the UI
    if (sanitizedValue === "") {
      onArgumentValueChange(name, isNullable ? null : undefined);
    }
  };

  const placeholder = `Enter number between ${range.min} and ${range.max}`;

  return (
    <TextInput
      name={name}
      label={name}
      value={displayValue}
      size="sm"
      isInvalid={isInvalid}
      placeholder={placeholder}
      tooltipText={tooltipText}
      errorMessage={errorMessage}
      onChange={handleChange}
      onFocus={handleFocus}
      onBlur={handleBlur}
    />
  );
};

export default ServiceArgumentNumberInput;
