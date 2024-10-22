// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentNumberInput.scss";

import classNames from "classnames";
import { ChangeEvent, useState } from "react";

import ServiceArgumentInputMessage from "@/components/admin-panel/control-plane/ServiceArgumentInputMessage/ServiceArgumentInputMessage";
import { ServiceArgumentInputValue } from "@/models/admin-panel/control-plane/serviceArgument";

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

  const validateInput = (value: string) => {
    if (nullable && value.trim() === "") {
      return false;
    } else {
      const isValidNumber = !isNaN(parseFloat(value));
      if (isValidNumber) {
        const numericValue = parseFloat(value);
        const isInRange =
          numericValue >= range.min && numericValue <= range.max;
        return !isInRange;
      } else {
        return true;
      }
    }
  };

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    setValue(event.target.value);
    const isNewValueInvalid = validateInput(event.target.value);
    setIsInvalid(isNewValueInvalid);
    onArgumentValidityChange(name, isNewValueInvalid);
    if (!isNewValueInvalid) {
      const newValue = parseFloat(event.target.value) || null;
      onArgumentValueChange(name, newValue);
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
      {isInvalid && (
        <ServiceArgumentInputMessage
          message={`Please enter a number between ${range.min} and ${range.max}`}
          forInvalid
        />
      )}
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
