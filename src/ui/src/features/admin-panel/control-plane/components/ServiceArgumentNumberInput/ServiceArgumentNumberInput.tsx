// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEvent, useEffect, useState } from "react";
import { ValidationError } from "yup";

import TextInput from "@/components/ui/TextInput/TextInput";
import { chatQnAGraphEditModeEnabledSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/features/admin-panel/control-plane/types";
import { validateServiceArgumentNumberInput } from "@/features/admin-panel/control-plane/validators/service-arguments/numberInput";
import { useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";
import { NumberInputRange } from "@/utils/validators/types";

export type ServiceArgumentNumberInputValue =
  | string
  | number
  | undefined
  | null;

interface ServiceArgumentNumberInputProps {
  name: string;
  initialValue: ServiceArgumentNumberInputValue;
  range: NumberInputRange;
  tooltipText?: string;
  isNullable?: boolean;
  isReadOnlyDisabled?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
  onArgumentValidityChange: OnArgumentValidityChangeHandler;
}

const ServiceArgumentNumberInput = ({
  name,
  initialValue,
  range,
  tooltipText,
  isNullable = false,
  isReadOnlyDisabled = false,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentNumberInputProps) => {
  const isGraphEditModeEnabled = useAppSelector(
    chatQnAGraphEditModeEnabledSelector,
  );
  const isEditModeEnabled = isReadOnlyDisabled
    ? isReadOnlyDisabled
    : isGraphEditModeEnabled;
  const isReadOnly = !isEditModeEnabled;

  const [value, setValue] = useState(initialValue || "");
  const [isInvalid, setIsInvalid] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (isReadOnly) {
      setValue(initialValue ?? "");
      setIsInvalid(false);
    }
  }, [isReadOnly, initialValue]);

  const validateInput = async (value: string) => {
    try {
      await validateServiceArgumentNumberInput(value, range, isNullable);
      setIsInvalid(false);
      setErrorMessage("");
      return true;
    } catch (validationError) {
      setIsInvalid(true);
      setErrorMessage((validationError as ValidationError).message);
      return false;
    }
  };

  const handleChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setValue(newValue);
    const sanitizedValue = sanitizeString(newValue);
    const isValid = await validateInput(sanitizedValue);
    onArgumentValidityChange(name, !isValid);
    if (isValid) {
      const argumentValue = parseFloat(sanitizedValue) || null;
      onArgumentValueChange(name, argumentValue);
    }
  };

  const placeholder = `Enter number between ${range.min} and ${range.max}`;

  return (
    <TextInput
      name={name}
      label={name}
      value={value}
      size="sm"
      isInvalid={isInvalid}
      isReadOnly={isReadOnly}
      placeholder={placeholder}
      tooltipText={tooltipText}
      errorMessage={errorMessage}
      onChange={handleChange}
    />
  );
};

export default ServiceArgumentNumberInput;
