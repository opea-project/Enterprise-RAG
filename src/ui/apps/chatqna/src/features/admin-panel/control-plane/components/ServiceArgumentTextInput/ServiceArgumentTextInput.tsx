// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { TextInput } from "@intel-enterprise-rag-ui/components";
import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEvent, useEffect, useState } from "react";
import { ValidationError } from "yup";

import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/features/admin-panel/control-plane/types";
import { validateServiceArgumentTextInput } from "@/features/admin-panel/control-plane/validators/service-arguments/textInput";

export type ServiceArgumentTextInputValue = string | string[] | null;

interface ServiceArgumentTextInputProps {
  name: string;
  value: ServiceArgumentTextInputValue;
  tooltipText?: string;
  isNullable?: boolean;
  isCommaSeparated?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
  onArgumentValidityChange: OnArgumentValidityChangeHandler;
}

const ServiceArgumentTextInput = ({
  name,
  value,
  tooltipText,
  isNullable = false,
  isCommaSeparated = false,
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
      await validateServiceArgumentTextInput(value, isNullable);
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

export default ServiceArgumentTextInput;
