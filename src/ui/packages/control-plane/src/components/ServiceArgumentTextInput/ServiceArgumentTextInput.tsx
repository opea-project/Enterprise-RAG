// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { TextInput } from "@intel-enterprise-rag-ui/components";
import { getValidationErrorMessage } from "@intel-enterprise-rag-ui/input-validation";
import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEvent, useEffect, useState } from "react";

import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
  ServiceArgumentTextInputValue,
} from "@/types/index";
import { validateServiceArgumentTextInput } from "@/validators/service-arguments/textInput";

interface ServiceArgumentTextInputProps {
  name: string;
  value: ServiceArgumentTextInputValue;
  tooltipText?: string;
  isNullable?: boolean;
  isCommaSeparated?: boolean;
  supportedValues?: string[];
  onArgumentValueChange: OnArgumentValueChangeHandler;
  onArgumentValidityChange: OnArgumentValidityChangeHandler;
}

export const ServiceArgumentTextInput = ({
  name,
  value,
  tooltipText,
  isNullable = false,
  isCommaSeparated = false,
  supportedValues,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentTextInputProps) => {
  const [displayValue, setDisplayValue] = useState(value ?? "");
  const [isInvalid, setIsInvalid] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    setDisplayValue(value ?? "");
  }, [value]);

  const validateInput = async (value: string) => {
    try {
      await validateServiceArgumentTextInput(
        value,
        isNullable,
        isCommaSeparated,
        supportedValues,
      );
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
    const isValid = await validateInput(sanitizedValue);
    setIsInvalid(!isValid);
    onArgumentValidityChange(name, !isValid);
    if (isValid) {
      const isValueEmpty = newValue.trim() === "";
      let argumentValue = null;
      if (!isValueEmpty) {
        argumentValue = isCommaSeparated
          ? sanitizedValue.split(",").map((value) => value.trim())
          : sanitizedValue;
      }
      onArgumentValueChange(name, argumentValue);
    }
  };

  const placeholder = isCommaSeparated ? "Enter values separated by comma" : "";

  return (
    <TextInput
      data-testid={`service-argument-text-input-${name}`}
      name={name}
      label={name}
      value={displayValue}
      size="sm"
      isInvalid={isInvalid}
      placeholder={placeholder}
      tooltipText={tooltipText}
      errorMessage={errorMessage}
      isCommaSeparated={isCommaSeparated}
      onChange={handleChange}
    />
  );
};
