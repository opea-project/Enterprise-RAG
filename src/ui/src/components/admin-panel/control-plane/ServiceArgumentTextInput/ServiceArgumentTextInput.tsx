// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentTextInput.scss";

import classNames from "classnames";
import { ChangeEvent, useState } from "react";
import * as Yup from "yup";
import { ValidationError } from "yup";

import ServiceArgumentInputMessage from "@/components/admin-panel/control-plane/ServiceArgumentInputMessage/ServiceArgumentInputMessage";
import { ServiceArgumentInputValue } from "@/models/admin-panel/control-plane/serviceArgument";
import { noEmpty } from "@/utils/validators";

interface ServiceArgumentTextInputProps {
  name: string;
  initialValue: string | null;
  emptyValueAllowed?: boolean;
  commaSeparated?: boolean;
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
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentTextInputProps) => {
  const [value, setValue] = useState(initialValue ?? "");
  const [isFocused, setIsFocused] = useState(false);
  const [isInvalid, setIsInvalid] = useState(false);
  const [error, setError] = useState("");

  const validationSchema = Yup.object().shape({
    textInput: Yup.string().test(
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
    const isValid = await validateInput(newValue);
    setIsInvalid(!isValid);
    onArgumentValidityChange(name, !isValid);
    if (isValid) {
      const isValueEmpty = newValue.trim() === "";
      const argumentValue = isValueEmpty && emptyValueAllowed ? null : newValue;
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
    "service-argument-text-input": true,
    "input--invalid": isInvalid,
  });

  const showCSTextInputMessage = commaSeparated && isFocused && !isInvalid;

  return (
    <div className="relative">
      {isInvalid && <ServiceArgumentInputMessage message={error} forInvalid />}
      {showCSTextInputMessage && (
        <ServiceArgumentInputMessage
          message="Please enter values separated by commas"
          forFocus
        />
      )}
      <input
        className={inputClassNames}
        type="text"
        name={`${name}-text-input`}
        value={value}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
      />
    </div>
  );
};

export default ServiceArgumentTextInput;
