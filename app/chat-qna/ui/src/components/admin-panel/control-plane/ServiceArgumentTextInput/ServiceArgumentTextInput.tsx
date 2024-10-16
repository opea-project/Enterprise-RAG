// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentTextInput.scss";

import classNames from "classnames";
import { ChangeEvent, useState } from "react";

import ServiceArgumentInputMessage from "@/components/admin-panel/control-plane/ServiceArgumentInputMessage/ServiceArgumentInputMessage";

interface ServiceArgumentTextInputProps {
  name: string;
  initialValue: string;
  onArgumentValueChange: (
    argumentName: string,
    argumentValue: string | number | boolean | null,
  ) => void;
  onArgumentValidityChange: (
    argumentName: string,
    isArgumentInvalid: boolean,
  ) => void;
}

const ServiceArgumentTextInput = ({
  name,
  initialValue,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentTextInputProps) => {
  const [value, setValue] = useState(initialValue);
  const [isInvalid, setIsInvalid] = useState(false);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const isValueEmpty = event.target.value.trim() === "";
    setIsInvalid(isValueEmpty);
    onArgumentValidityChange(name, isValueEmpty);
    setValue(event.target.value);
    if (!isValueEmpty) {
      onArgumentValueChange(name, event.target.value);
    }
  };

  const inputClassNames = classNames({
    "service-argument-text-input": true,
    "input--invalid": isInvalid,
  });

  return (
    <div className="relative">
      {isInvalid && (
        <ServiceArgumentInputMessage
          message="This value cannot be empty"
          forInvalid
        />
      )}
      <input
        className={inputClassNames}
        type="text"
        name={`${name}-text-input`}
        value={value}
        onChange={handleChange}
      />
    </div>
  );
};

export default ServiceArgumentTextInput;
