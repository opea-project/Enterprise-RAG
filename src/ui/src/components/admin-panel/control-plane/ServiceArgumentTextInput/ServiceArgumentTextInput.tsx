// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentTextInput.scss";

import classNames from "classnames";
import { ChangeEvent, useState } from "react";

import ServiceArgumentInputMessage from "@/components/admin-panel/control-plane/ServiceArgumentInputMessage/ServiceArgumentInputMessage";
import { ServiceArgumentInputValue } from "@/models/admin-panel/control-plane/serviceArgument";

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

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const isValueEmpty = event.target.value.trim() === "";
    const isInvalid = emptyValueAllowed ? false : isValueEmpty;
    setIsInvalid(isInvalid);
    onArgumentValidityChange(name, isInvalid);
    setValue(event.target.value);
    if (!isInvalid) {
      let argumentValue: string | null = event.target.value;
      if (isValueEmpty && emptyValueAllowed) {
        argumentValue = null;
      }
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
      {isInvalid && (
        <ServiceArgumentInputMessage
          message="This value cannot be empty"
          forInvalid
        />
      )}
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
