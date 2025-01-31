// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentNumberInput.scss";

import classNames from "classnames";
import { ChangeEvent, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { object, string, ValidationError } from "yup";

import { ServiceArgumentInputValue } from "@/models/admin-panel/control-plane/serviceArgument";
import { sanitizeString } from "@/utils";
import { isInRange } from "@/utils/validators/textInput";

interface ServiceArgumentNumberInputProps {
  name: string;
  initialValue: number | null;
  range: { min: number; max: number };
  nullable?: boolean;
  readOnly?: boolean;
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
  readOnly = false,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentNumberInputProps) => {
  const [value, setValue] = useState<number | string>(initialValue || "");
  const [isInvalid, setIsInvalid] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (readOnly) {
      setValue(initialValue ?? "");
      setIsInvalid(false);
    }
  }, [readOnly, initialValue]);

  const validationSchema = object().shape({
    numberInput: string().test(
      "is-in-range",
      `Enter number between ${range.min} and ${range.max}`,
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

  const inputClassNames = classNames({
    "service-argument-number-input": true,
    "input--invalid": isInvalid,
  });

  const inputId = `${name}-number-input-${uuidv4()}`;
  const placeholder = `Enter number between ${range.min} and ${range.max}`;

  return (
    <>
      <label htmlFor={inputId} className="service-argument-number-input__label">
        {name}
      </label>
      <input
        className={inputClassNames}
        value={value}
        id={inputId}
        name={inputId}
        type="text"
        placeholder={placeholder}
        readOnly={readOnly}
        onChange={handleChange}
      />
      {isInvalid && <p className="error my-1 pl-2 text-xs italic">{error}</p>}
    </>
  );
};

export default ServiceArgumentNumberInput;
