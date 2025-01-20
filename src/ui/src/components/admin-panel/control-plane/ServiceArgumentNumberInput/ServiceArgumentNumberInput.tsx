// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentNumberInput.scss";

import classNames from "classnames";
import { ChangeEvent, useState } from "react";
import { object, string, ValidationError } from "yup";

import ServiceArgumentInputMessage from "@/components/admin-panel/control-plane/ServiceArgumentInputMessage/ServiceArgumentInputMessage";
import { ServiceArgumentInputValue } from "@/models/admin-panel/control-plane/serviceArgument";
import { sanitizeString } from "@/utils";
import { isInRange } from "@/utils/validators/textInput";

interface ServiceArgumentNumberInputProps {
  name: string;
  initialValue: number | null;
  range: { min: number; max: number };
  nullable?: boolean;
  onArgumentValueChange: (
    argumentName: string,
    argumentValue: ServiceArgumentInputValue,
  ) => void;
  onArgumentValidityChange: (
    argumentName: string,
    isArgumentInvalid: boolean,
  ) => void;
}

const ServiceArgumentNumberInput = ({
  name,
  initialValue,
  range,
  nullable = false,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentNumberInputProps) => {
  const [value, setValue] = useState<number | string>(initialValue || "");
  const [isFocused, setIsFocused] = useState(false);
  const [isInvalid, setIsInvalid] = useState(false);
  const [error, setError] = useState("");

  const validationSchema = object().shape({
    numberInput: string().test(
      "is-in-range",
      `Please enter a number between ${range.min} and ${range.max}`,
      isInRange(nullable, range),
    ),
  });

  const validateInput = async (value: string) => {
    try {
      await validationSchema.validate({ numberInput: value });
      setIsInvalid(false);
      setError("");
      return true;
    } catch (validationError) {
      setIsInvalid(true);
      setError((validationError as ValidationError).message);
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

  const handleFocus = () => {
    setIsFocused(true);
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  const inputClassNames = classNames({
    "service-argument-number-input": true,
    "input--invalid": isInvalid,
  });

  return (
    <div className="relative">
      {isFocused && !isInvalid && (
        <ServiceArgumentInputMessage
          message={`Please enter a number between ${range.min} and ${range.max}`}
          forFocus
        />
      )}
      {isInvalid && <ServiceArgumentInputMessage message={error} forInvalid />}
      <input
        className={inputClassNames}
        type="text"
        name={`${name}-number-input`}
        value={value}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
      />
    </div>
  );
};

export default ServiceArgumentNumberInput;
