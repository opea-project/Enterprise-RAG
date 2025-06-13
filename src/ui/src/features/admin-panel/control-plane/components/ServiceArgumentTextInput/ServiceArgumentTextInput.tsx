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
import { validateServiceArgumentTextInput } from "@/features/admin-panel/control-plane/validators/service-arguments/textInput";
import { useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";

export type ServiceArgumentTextInputValue = string | string[] | null;

interface ServiceArgumentTextInputProps {
  name: string;
  initialValue: ServiceArgumentTextInputValue;
  tooltipText?: string;
  isNullable?: boolean;
  isCommaSeparated?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
  onArgumentValidityChange: OnArgumentValidityChangeHandler;
}

const ServiceArgumentTextInput = ({
  name,
  initialValue,
  tooltipText,
  isNullable = false,
  isCommaSeparated = false,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentTextInputProps) => {
  const isEditModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);
  const isReadOnly = !isEditModeEnabled;

  const [value, setValue] = useState(initialValue ?? "");
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
    setValue(newValue);
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
      value={value}
      size="sm"
      isInvalid={isInvalid}
      isReadOnly={isReadOnly}
      placeholder={placeholder}
      tooltipText={tooltipText}
      errorMessage={errorMessage}
      isCommaSeparated={isCommaSeparated}
      onChange={handleChange}
    />
  );
};

export default ServiceArgumentTextInput;
