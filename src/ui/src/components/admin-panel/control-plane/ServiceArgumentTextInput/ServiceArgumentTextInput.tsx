// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentTextInput.scss";

import classNames from "classnames";
import { ChangeEvent, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { object, string, ValidationError } from "yup";

import { ServiceArgumentInputValue } from "@/models/admin-panel/control-plane/serviceArgument";
import { sanitizeString } from "@/utils";
import { noEmpty } from "@/utils/validators/textInput";

interface ServiceArgumentTextInputProps {
  name: string;
  initialValue: string | null;
  emptyValueAllowed?: boolean;
  commaSeparated?: boolean;
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

const ServiceArgumentTextInput = ({
  name,
  initialValue,
  emptyValueAllowed = false,
  commaSeparated = false,
  readOnly = false,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentTextInputProps) => {
  const [value, setValue] = useState(initialValue ?? "");
  const [isInvalid, setIsInvalid] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (readOnly) {
      setValue(initialValue ?? "");
      setIsInvalid(false);
    }
  }, [readOnly, initialValue]);

  const validationSchema = object().shape({
    textInput: string().test(
      "no-empty",
      "This value cannot be empty",
      noEmpty(emptyValueAllowed),
    ),
  });

  const validateInput = async (value: string) => {
    try {
      await validationSchema.validate({ textInput: value });
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
    setIsInvalid(!isValid);
    onArgumentValidityChange(name, !isValid);
    if (isValid) {
      const isValueEmpty = newValue.trim() === "";
      const argumentValue =
        isValueEmpty && emptyValueAllowed ? null : sanitizedValue;
      onArgumentValueChange(name, argumentValue);
    }
  };

  const inputClassNames = classNames({
    "service-argument-text-input": true,
    "input--invalid": isInvalid,
  });

  const inputId = `${name}-text-input-${uuidv4()}`;
  const placeholder = commaSeparated ? "Enter values separated by comma" : "";

  return (
    <>
      <label htmlFor={inputId} className="service-argument-text-input__label">
        {name}
      </label>
      <input
        className={inputClassNames}
        type="text"
        id={inputId}
        name={inputId}
        value={value}
        placeholder={placeholder}
        readOnly={readOnly}
        onChange={handleChange}
      />
      {isInvalid && <p className="error my-1 pl-2 text-xs italic">{error}</p>}
    </>
  );
};

export default ServiceArgumentTextInput;
